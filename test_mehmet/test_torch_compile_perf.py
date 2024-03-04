# bench.py
import torch
from transformers import MobileBertForQuestionAnswering
import intel_extension_for_pytorch as ipex

# Initialize an eager model
model = MobileBertForQuestionAnswering.from_pretrained("csarron/mobilebert-uncased-squad-v2")
seq_length = 128
bs = 128
vocab_size = model.config.vocab_size
input = torch.randint(0, vocab_size, (bs, seq_length), dtype=torch.int64)
input_dict = {"input_ids": input}


model = ipex.optimize(model, weights_prepack=False)

# Initialize the inductor model
compiled_model = torch.compile(model, backend="ipex")
with torch.no_grad():
    compiled_model(**input_dict)



# NUM_ITERS=10
# import timeit
# with torch.no_grad():
#     # warmup
#     for _ in range(10):
#         model(**input_dict)
#     eager_t = timeit.timeit("model(**input_dict)", number=NUM_ITERS, globals=globals())

# with torch.no_grad():
#     # warmup
#     for _ in range(10):
#         compiled_model(**input_dict)
#     inductor_t = timeit.timeit("compiled_model(**input_dict)", number=NUM_ITERS, globals=globals())
# print(f"eager use: {eager_t * 1000 / NUM_ITERS} ms/iter")
# print(f"inductor use: {inductor_t * 1000 / NUM_ITERS} ms/iter")
# print(f"speed up ratio: {eager_t / inductor_t}")





from torch.profiler import profile, schedule, ProfilerActivity
RESULT_DIR = "./prof_trace"
my_schedule = schedule(
    skip_first=1,
    wait=1,
    warmup=5,
    active=1,
    repeat=1)

def trace_handler(p):
    output = p.key_averages().table(sort_by="self_cpu_time_total")#, row_limit=20)
    print(output)
    p.export_chrome_trace(f"{RESULT_DIR}/{p.step_num}.json")

for _ in range(3):
    compiled_model(**input_dict)  # compiled_model(**input_dict) to get inductor model profiling

total = 0
with profile(
    activities=[ProfilerActivity.CPU],
    schedule=my_schedule,
    on_trace_ready=trace_handler
) as p:
    for _ in range(10):
        compiled_model(**input_dict)  # compiled_model(**input_dict) to get inductor model profiling
        p.step()