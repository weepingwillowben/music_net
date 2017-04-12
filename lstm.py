import string
import theano
import numpy as np
import theano.tensor as T
import plot_utility
import itertools
import gc
import time
from WeightBias import WeightBias
from shared_save import RememberSharedVals
import string_processing

#theano.config.optimizer="fast_compile"
#theano.config.scan.allow_gc=True

SEQUENCE_LEN = 8

BATCH_SIZE = 128
EPOCS = 50

IN_LEN = string_processing.CHARS_LEN
OUT_LEN = 600
CELL_STATE_LEN = OUT_LEN
HIDDEN_LEN = OUT_LEN + IN_LEN

FULL_OUT_LEN =string_processing.CHARS_LEN

TRAIN_UPDATE_CONST = np.float32(0.1)

inputs = T.tensor3("inputs",dtype="float32")
expected_vec = T.matrix('expected',dtype="float32")
stateful_input_vec = T.vector('stateful_input')

cell_forget_fn = WeightBias("cell_forget", HIDDEN_LEN, CELL_STATE_LEN,1.0)
add_barrier_fn = WeightBias("add_barrier", HIDDEN_LEN, CELL_STATE_LEN,0.5)
add_cell_fn = WeightBias("add_cell", HIDDEN_LEN, CELL_STATE_LEN,0.0)
to_new_output_fn = WeightBias("to_new_hidden", HIDDEN_LEN, CELL_STATE_LEN,0.5)

full_output_fn = WeightBias("full_output", CELL_STATE_LEN, FULL_OUT_LEN,0.0)

train_plot_util = plot_utility.PlotHolder("train_test")
train_plot_util.add_plot("cell_forget_bias",cell_forget_fn.b,1000)
predict_plot_util = plot_utility.PlotHolder("predict_view")

shared_value_saver = RememberSharedVals('lstm_wbs_huck_fin5')

weight_biases = (
    cell_forget_fn.wb_list() +
    add_barrier_fn.wb_list() +
    add_cell_fn.wb_list() +
    to_new_output_fn.wb_list() +
    full_output_fn.wb_list()
)

def calc_outputs(in_vec,cell_state,out_vec):
    hidden_input = T.concatenate([out_vec,in_vec],axis=0)

    #first stage, forget some info
    cell_mul_val = T.nnet.sigmoid(cell_forget_fn.calc_output_batched(hidden_input))
    forgot_cell_state = cell_state * cell_mul_val

    #second stage, add some new info
    add_barrier = T.nnet.sigmoid(add_barrier_fn.calc_output_batched(hidden_input))
    this_add_val = T.tanh(add_cell_fn.calc_output_batched(hidden_input))
    added_cell_state = forgot_cell_state + this_add_val * add_barrier

    #third stage, get output
    out_all = T.nnet.sigmoid(to_new_output_fn.calc_output_batched(hidden_input))
    new_output = out_all * T.tanh(added_cell_state)

    return added_cell_state,new_output

def calc_error(expected, actual):
    sqrtdiff = (expected - actual)
    diff = sqrtdiff * sqrtdiff
    error = diff.sum()
    return error

def my_scan(invecs):
    [all_cell,all_out],updates = theano.scan(
        calc_outputs,
        sequences=[invecs],
        outputs_info=[
            dict(initial=T.zeros((OUT_LEN,BATCH_SIZE)),taps=[-1]),
            dict(initial=T.zeros((OUT_LEN,BATCH_SIZE)),taps=[-1])
            ],
        n_steps=SEQUENCE_LEN
    )
    return all_cell[-1],all_out[-1]

def get_batched_train_pred():
    out_cell_state,new_out = my_scan(inputs)
    predict_plot_util.add_plot("cell_state",out_cell_state,1000)

    true_out = T.tanh(full_output_fn.calc_output_batched(new_out))

    error = calc_error(true_out,expected_vec)
    train_plot_util.add_plot("error_mag",error)

    shared_value_saver.add_shared_vals(weight_biases)
    all_grads = T.grad(error,wrt=weight_biases)

    def rms_prop_updates():
        DECAY_RATE = np.float32(0.9)
        LEARNING_RATE = np.float32(0.1)
        STABILIZNG_VAL = np.float32(0.00001)

        gsqr = sum(T.sum(g*g) for g in all_grads)

        grad_sqrd_mag = theano.shared(np.float32(400),"grad_sqrd_mag")
        shared_value_saver.add_shared_val(grad_sqrd_mag)

        grad_sqrd_mag_update = DECAY_RATE * grad_sqrd_mag + (np.float32(1)-DECAY_RATE)*gsqr

        wb_update_mag = LEARNING_RATE / T.sqrt(grad_sqrd_mag_update + STABILIZNG_VAL)
        train_plot_util.add_plot("update_mag",wb_update_mag)

        wb_update = [(wb,wb - wb_update_mag * grad) for wb,grad in zip(weight_biases,all_grads)]
        return wb_update + [(grad_sqrd_mag,grad_sqrd_mag_update)]

    updates = rms_prop_updates()

    # Normal SGD
    #grads = T.grad(error,wrt=weight_biases)
    #updates = [(sh_var,sh_var - TRAIN_UPDATE_CONST*grad) for sh_var,grad in zip(weight_biases,grads)]


    predict_fn = theano.function(
        [inputs],
        predict_plot_util.append_plot_outputs([true_out])
    )

    train_fn = theano.function(
        [inputs,expected_vec],
        train_plot_util.append_plot_outputs([]),
        updates=updates
    )
    return predict_fn, train_fn

'''
predict_fn,train_fn = get_batched_train_pred()

train_str = string_processing.get_str("data/huck_fin.txt")
in_vec_list = string_processing.in_vec(train_str)


print(train_str)
instr = np.transpose(np.vstack(in_vec_list))
print(instr.shape)
def output_trains(num_trains):
    for i in range(num_trains):
        for mid in range(SEQUENCE_LEN,len(train_str)-BATCH_SIZE-1,BATCH_SIZE):
            start = mid - SEQUENCE_LEN
            end = mid + BATCH_SIZE
            in3dtens = np.dstack([instr[:,mid+j:end+j] for j in range(-SEQUENCE_LEN+1,1)] )
            in3dtens = np.rollaxis(in3dtens,-1)
            expected = instr[:,mid+1:end+1]
            yield in3dtens,expected
        print("train_epoc"+str(i),flush=True)
        #for i in range(5): gc.collect()

def train():
    num_trains = 0
    time_last = time.clock()
    train_time = 0
    for inpt,expect in output_trains(EPOCS):
        start = time.clock()
        blocks = train_fn(inpt,expect)
        train_time += time.clock() - start
        output = to_numpys(blocks)
        train_plot_util.update_plots(output)
        shared_value_saver.vals_updated()
        if num_trains%50==0:
            now = time.clock()
            print("train update took {}".format(now-time_last),flush=True)
            print("train time was {}".format(train_time))
            time_last = now
            train_time = 0
        num_trains += 1

    shared_value_saver.force_update()

def to_numpys(outlist):
    return [np.asarray(o) for o in outlist]

def predict():
    pred_text = []
    for inp,_ in output_trains(1):
        outputs = to_numpys(predict_fn(inp))
        predict_plot_util.update_plots(outputs)

        pred_text.append(outputs[0])

    text = [let for t in pred_text for let in np.transpose(t) ]

    outtxt = string_processing.out_list_to_str(text)

    return outtxt

train()
print(predict())
'''
