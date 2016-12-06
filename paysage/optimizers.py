import numpy    

    
# ----- OPTIMIZERS ----- #        
        
class StochasticGradientDescent(object):
    """StochasticGradientDescent
       Basic algorithm of gradient descent with minibatches. 
    
    """
    def __init__(self, model, stepsize=0.001, lr_decay=0.5):
        self.lr_decay = lr_decay
        self.stepsize = stepsize
        self.grad = {key: numpy.zeros_like(model.params[key]) for key in model.params}
    
    def update(self, model, v_data, v_model, epoch):
        lr = self.lr_decay ** epoch
        self.grad = gradient(model, v_data, v_model)
        for key in self.grad:
            model.params[key][:] = model.params[key] - lr * self.stepsize * self.grad[key]
         
         
class Momentum(object):
    """Momentum
       Stochastic gradient descent with momentum.
       Qian, N. (1999). On the momentum term in gradient descent learning algorithms. Neural Networks : The Official Journal of the International Neural Network Society, 12(1), 145–151
    
    """
    def __init__(self, model, stepsize=0.001, momentum=0.9, lr_decay=0.5):
        self.lr_decay = lr_decay
        self.stepsize = stepsize
        self.momentum = momentum
        self.grad = {key: numpy.zeros_like(model.params[key]) for key in model.params}
        self.delta = {key: numpy.zeros_like(model.params[key]) for key in model.params}
    
    def update(self, model, v_data, v_model, epoch):
        lr = self.lr_decay ** epoch
        self.grad = gradient(model, v_data, v_model)
        for key in self.grad:
            self.delta[key][:] = self.grad[key] + self.momentum * self.delta[key]
            model.params[key][:] = model.params[key] - lr * self.stepsize * self.delta[key]


class RMSProp(object):
    """RMSProp
       Geoffrey Hinton's Coursera Course Lecture 6e
    
    """
    def __init__(self, model, stepsize=0.001, mean_square_weight=0.9):
        self.stepsize = stepsize
        self.mean_square_weight = mean_square_weight
        self.grad = {key: numpy.zeros_like(model.params[key]) for key in model.params}
        self.mean_square_grad = {key: numpy.zeros_like(model.params[key]) for key in model.params}
        self.epsilon = 10**-6
    
    def update(self, model, v_data, v_model, epoch):
        self.grad = gradient(model, v_data, v_model)
        for key in self.grad:
            self.mean_square_grad[key] = self.mean_square_weight * self.mean_square_grad[key] + (1-self.mean_square_weight)*self.grad[key]**2
            model.params[key][:] = model.params[key] - self.stepsize * self.grad[key] / numpy.sqrt(self.epsilon + self.mean_square_grad[key])


class ADAM(object):
    """ADAM
       Adaptive Moment Estimation algorithm. 
       Kingma, D. P., & Ba, J. L. (2015). Adam: a Method for Stochastic Optimization. International Conference on Learning Representations, 1–13.
    
    """
    def __init__(self, model, stepsize=0.001, mean_weight=0.9, mean_square_weight=0.9):
        self.stepsize = stepsize
        self.mean_weight = mean_weight
        self.mean_square_weight = mean_square_weight
        self.grad = {key: numpy.zeros_like(model.params[key]) for key in model.params}
        self.mean_square_grad = {key: numpy.zeros_like(model.params[key]) for key in model.params}
        self.mean_grad = {key: numpy.zeros_like(model.params[key]) for key in model.params}
        self.epsilon = 10**-6
    
    def update(self, model, v_data, v_model, epoch):
        self.grad = gradient(model, v_data, v_model)
        for key in self.grad:
            self.mean_square_grad[key] = self.mean_square_weight * self.mean_square_grad[key] + (1-self.mean_square_weight)*self.grad[key]**2
            self.mean_grad[key] = self.mean_weight * self.mean_grad[key] + (1-self.mean_weight)*self.grad[key]            
            model.params[key][:] = model.params[key] - (self.stepsize / (1 - self.mean_weight)) * self.mean_grad[key] / numpy.sqrt(self.epsilon + self.mean_square_grad[key] / (1 - self.mean_square_weight))
         
         
# ----- ALIASES ----- #
         
sgd = SGD = StochasticGradientDescent   
momentum = Momentum   
rmsprop = RMSProp   
adam = ADAM
        

# ----- FUNCTIONS ----- #

# gradient: (LatentModel, numpy.ndarray, numpy.ndarray) -> numpy.ndarray
def gradient(model, minibatch, samples):    
    positive_phase = model.derivatives(minibatch.astype(numpy.float32))
    negative_phase = model.derivatives(samples.astype(numpy.float32))
    return {key: (positive_phase[key] - negative_phase[key]) for key in positive_phase} 
        