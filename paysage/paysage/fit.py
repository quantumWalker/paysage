from . import models
from . import batch
from . import optimizers
import numpy
from numba import jit
    
# -----  CLASSES ----- #

class SequentialMC(object):
    
    def __init__(self, amodel, adataframe):
        self.model = amodel
        try:
            self.state = adataframe.as_matrix().astype(numpy.float32)
        except Exception:
            self.state = adataframe.astype(numpy.float32)
        
    @classmethod
    def from_batch(cls, amodel, abatch):
        tmp = cls(amodel, abatch.get())
        abatch.reset()
        return tmp
        
    def update_state(self, steps):
        self.state[:] = self.model.gibbs_chain(self.state, steps)

    #TODO: move resampling into the model class so that it can be alternated with gibbs
    def resample_state(self, temperature=1.0):
        energies = self.model.marginal_energy(self.state)
        weights = importance_weights(energies, numpy.float32(temperature)).clip(min=0.0)
        indices = numpy.random.choice(numpy.arange(len(self.state)), size=len(self.state), replace=True, p=weights)
        self.state[:] = self.state[list(indices)]        


class TrainingMethod(object):
    
    def __init__(self, model, abatch, optimizer, epochs, skip=100):
        self.model = model
        self.batch = abatch
        self.epochs = epochs
        self.sampler = SequentialMC.from_batch(self.model, self.batch)
        self.optimizer = optimizer
        self.monitor = ProgressMonitor(skip, self.batch)

        
class ContrastiveDivergence(TrainingMethod):
    
    def __init__(self, model, abatch, optimizer, epochs, mcsteps, skip=100):
        super().__init__(model, abatch, optimizer, epochs, skip=skip)
        self.mcsteps = mcsteps
        
    def train(self):
        for epoch in range(self.epochs):          
            t = 0
            while True:
                try:
                    v_data = self.batch.get(mode='train')
                except StopIteration:
                    break
                            
                # CD resets the sampler from the visible data at each iteration
                sampler = SequentialMC(self.model, v_data) 
                sampler.update_state(self.mcsteps)    
                
                # compute the gradient and update the model parameters
                self.optimizer.update(self.model, v_data, sampler.state, epoch)
                
                # monitor learning progress
                prog = self.monitor.check_progress(self.model, t)
                if prog:
                    print('Batch {0}: Reconstruction Error: {1:.6f}, Energy Distance: {2:.6f}'.format(t, *prog))
                t += 1
            # end of epoch processing
            prog = self.monitor.check_progress(self.model, 0)
            print('End of epoch {}: '.format(epoch))
            print("-Reconstruction Error: {0:.6f}, Energy Distance: {1:.6f}".format(*prog))
        
        return None
             
             
class ProgressMonitor(object):
    
    def __init__(self, skip, abatch, update_steps=10):
        self.skip = skip
        self.batch = abatch
        self.steps = update_steps
        self.num_validation_samples = self.batch.index.end['validate'] - self.batch.index.end['train']

    def reconstruction_error(self, model, v_data):
        sampler = SequentialMC(model, v_data) 
        sampler.update_state(1)   
        return numpy.sum((v_data - sampler.state)**2)
        
    def energy_distance(self, model, v_data):
        v_model = model.random(v_data)
        sampler = SequentialMC(model, v_model) 
        sampler.update_state(self.steps)
        sampler.resample_state(temperature=1.0)
        return len(v_model) * energy_distance(v_data, sampler.state)
        
    def check_progress(self, model, t):
        if not (t % self.skip):
            recon = 0
            edist = 0
            while True:
                try:
                    v_data = self.batch.get(mode='validate')
                except StopIteration:
                    break
                recon += self.reconstruction_error(model, v_data)
                edist += self.energy_distance(model, v_data)
            recon = numpy.sqrt(recon / self.num_validation_samples)
            edist = edist / self.num_validation_samples
            return recon, edist
    

# ----- ALIASES ----- #
         
        

# ----- FUNCTIONS ----- #

@jit('float32[:](float32[:])',nopython=True)
def normalize(anarray):
    return anarray / numpy.sum(numpy.abs(anarray))
    
@jit('float32[:](float32[:],float32)',nopython=True)
def importance_weights(energies, temperature):
    gauge = energies - numpy.min(energies)
    return normalize(numpy.exp(-gauge/temperature))   
    
@jit('float32(float32[:,:],float32[:,:])',nopython=True)
def energy_distance(minibatch, samples):
    d1 = numpy.float32(0)
    d2 = numpy.float32(0)
    d3 = numpy.float32(0)

    for i in range(len(minibatch)):
        for j in range(len(minibatch)):
            d1 += numpy.linalg.norm(minibatch[i] - minibatch[j])
    d1 = d1 / (len(minibatch)**2 - len(minibatch))
    
    for i in range(len(samples)):
        for j in range(len(samples)):
            d2 += numpy.linalg.norm(samples[i] - samples[j])
    d2 = d2 / (len(samples)**2 - len(samples))
    
    for i in range(len(minibatch)):
        for j in range(len(samples)):
            d3 += numpy.linalg.norm(minibatch[i] - samples[j])
    d3 = d3 / (len(minibatch)*len(samples))
    
    return 2*d3 - d2 - d1
        