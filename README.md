#Creating long term memory for a neural network


## Introduction

### Assumed Knowledge

Now, to start off, I am no expert in neural nets. I spent a month or two learning about them from excellent sources like [this](http://neuralnetworksanddeeplearning.com/).

If you have a good understanding of linear algebra and multidimensional calculus, you should be able to pick it up quite quickly. But neural nets do not use super advanced mathematical concepts, so don't let the math scare you too much! You should be able to learn the math alongside the network specific info. Why am I going over this? Because for this post, I will assume some basic knowledge about neural nets. There are already a million sources to learn the basics, and far too few going over more advanced concepts.

### Inspiration and Goal

To start out, I will cover LSTMs, as they are the base for what I am trying to do. There is an awesome description of them [here](http://colah.github.io/posts/2015-08-Understanding-LSTMs/), and I will be using diagrams from that source (which are generously published as public domain).

One thing to know about LSTMs is that they are invented in 1999, and are still by far the best general purpose time series predictor known. This is not due to a lack of effort. There have been advances in

* Mathematics: Hessian free optimization, an  effective second order optimization model, has been successfully applied to neural networks)
* Neuroscience: We have a much better idea of how neurons actually interact)
Recurrent neural network design: Inspired by LSTMs, many people have created similar models which they though would solve some problems that LSTMs seem to have. None of the dozens of these are better, although some are marginally simpler. A meta-study done recently found that some models are marginally better.
* Augmented networks: Many people think the next big thing in neural nets are ones given external memory to work with. These are often combined with LSTM networks on some of the most important pattern recognition problems. Google's new translation algorithm uses Attention networks to augment LSTMs.


So what makes these so powerful? What made people think they could be improved with minor changes, and why were they wrong? What can't it do? If we ever want to make something even better, perhaps solving some of the problems with LSTMs, we need to be able to answer these questions. I think that LSTMs might encode something fundamental about how human intelligence works, although it may not be easy to see what that is.

Because solving problems is easier than figuring out fundamental reasons for phenomena, I also want to explore how one might improve LSTMs. Attention based networks have made significant strides in time sequence analysis, such as translation. But current methods are inefficient for long time series. One potential goal of a lower level network model is to condense the important information in a long time series into a relatively small number of steps, each of which containing a reasonable amount of information. In other words, to compress the time scale of the data, without hugely increasing the spatial scale. It is not clear that current tequniques like stacking LSTMS do this effectively.

I think that this condensation over time is vital to creating human level intelligence. The very idea of attention is related to the conscious self, which can only focus on a small number of things at a time. So it relies on something lower level to condense the relevant information to something we can reasonably expect the machine to focus on.

### Recurrent Networks and Time Sequence Learning

First, what is a recurrent network? It tries to solve a common problem that humans solve, which is recognizing or generating sequences over time. So, a recurrent network looks at things like songs or text one time unit at a time. For example, RNNs are used for voice recognition, i.e. turning a sequence of sound waves into a sequence of letters.

A recurrent network broadly it looks like this:

The major parts are the input, a state which is a function of the previous inputs, and the output, which is a function of the previous state. For voice recognition, the output would then be compared to the expected output, which is usually computed by hand (by writing out the text that the person is saying). Then, as long as the function A is differentiable, we can use backpropagation with gradient descent. While I won't go too deep into gradient descent, I will mention what it looks like. We store the inputs and states for several time steps back. Then we attempt to find out which internal parameters in the function contributed to the output the most. We then change these parameters so that they make the function output what we expected it to. To help conceptualize this, look at the diagram above. Suppose h3 is purely a function of x0 and x1. Then we would want to change the parameters in the A function so that this occurs.

So how do we construct such a function so that we can nicely change the parameters like that? The obvious construction follows directly from ordinary deep neural networks.

#### Description of ordinary recurrent networks
#### Why ordinary RNNs fail
cite http://www-dsi.ing.unifi.it/~paolo/ps/tnn-94-gradient.pdf
#### Description of LSTM networks
#### Some broad intuition for why they might work better

## Execution and Debugging of Neural Network Code

### Theano

Ok, now on to creating the code. I chose Theano, which I think is a really cool framework, independent of all the cool neural networks it allows you to build. Basically, it view the program as a graph. This allows the following:

* Manipulate the program graph in order to make the code faster.
    * memory reuse optimization
* Hardware support
    * Very easy and efficient GPU computation
    * cluster computation, including muti-GPU computation
* Allows for easy generation of code flow charts
* Automatic and efficient computation of gradients, saving a lot of code

Unfortunately, it comes with the downside that the code creation and execution are more separated than usual, making it somewhat harder to debug. Luckily, the Theano developers put a lot of work into making this problem better.

### Thoughts on Debugging

Now, when people show you their neural network code, you go off happy, and try to run it, and it may work, but good luck making any changes. Neural nets are notoriously tricky. Out of all the code I have ever written, they have the greatest barriers to debugging. The code will run with several major errors, but it will not do what you want to do without everything being perfect. I this is an interesting contrast to standard AI techniques, which may be fiddly, but if you make one minor error in the code, then usually most things work fine, or it crashes immediately, or at the very least, it is easy to trace back what exactly went wrong. In general, it is easy to debug.

This leads me to think that neural nets require an entirely different view of computation than symbolic AI. For GOFAI, we are navigating around some sort of finite state machine, or some sort of symbol processor, or decision tree, or something, and in all of these, we can think about the program moving around, doing different things in different cases. For neural nets, there are no conditionals in the main part of the code. You can write out just about every ANN ever invented without loops, if statements or recursion. This is not only speculation or theory, some code I wrote does just this, outputting code without loops that computes a simple neural net.

To summarize: in neural networks, data is the only thing being changed.

I think this is a fundamental difference in software thought, which requires new debugging tools, new tests, new debugging thought processes, and maybe even new hardware. Instead of thinking about an instruction pointer going around, we need to think about data changing, its interactions with data around it, how it accumulates, increments, and compounds. We need visualizations which allows us to see how the data is changing, not which instruction the computer is following.

In order to accomplish this, I made a tools that save values in the network to a file, and a tool which uses MatPlotlib to create a visualization of that data. More about this later.

## Actual Implementations and Some Results

### First Neural Net

To get back into practice with neural nets, and accustomize myself to the working of Theano, I made an extremely simple 3 layer neural net, and trained it on an extremely simple learning task. The task was to learn a Caesar cipher of 1, that is the letters A,B,C,...,Y,Z turns into B,C,D,...,Z,A. Even though this is a trivial learning task, it reveals some interesting facts about neural networks and gradient descent.

#### Random initialization bug

Plot1--changes in biases after long period of time

Batching

Optimizers

plot2 changes in biases with optimizer

### LSTM

Now, back to the main goal of creating a network that has some understanding of text.

I will start out with a rather simple learning task: recognize most likely next letter.

For example, if it gets input "I am goin", it should output "g", as it is pretty obvious that the statement is: "I am going".

Amazingly, my first successful run produced somewhat OK results, with most
