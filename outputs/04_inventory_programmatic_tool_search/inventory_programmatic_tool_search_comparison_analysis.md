# Programmatic Tool Calling vs. Programmatic Tool Calling + Tool Search

- Source notebook: `notebooks/04_inventory_programmatic_tool_search.ipynb`
- Source execution cell: 8 (`repeated-comparison`)
- Source results: [small dataset](inventory_small_catalog_100_repeated_cold_write_and_warm_read_protocol.md), [medium dataset](inventory_medium_catalog_100_repeated_cold_write_and_warm_read_protocol.md)
- Dataset name: `inventory`
- Dataset sizes: `small (3 SKUs, 9 required tool calls)`, `medium (10 SKUs, 30 required tool calls)`
- Compared arms: `programmatic_eager`, `programmatic_tool_search`
- Model: `gpt-5.6`
- Catalog size: `100` functions
- Repetitions per arm and dataset: `3`
- Cache phases per repetition: `cold_write`, `warm_read`
- Runs analyzed: `24` (2 datasets × 2 arms × 3 repetitions × 2 cache phases)
- Execution date: `2026-08-14` (`Asia/Seoul`)

Both experiments use `gpt-5.6`, a catalog of 100 functions, three repetitions per arm,
and an explicit cold/write followed by warm/read cache protocol. The small dataset has
3 SKUs and requires 9 function calls per run; the medium dataset has 10 SKUs and
requires 30 function calls per run.

## Aggregate comparison

The values below are means across the three repetitions for each cache phase. The
overall cost and latency changes compare all six runs per arm.

| Dataset | Cache phase | Eager input tokens | Tool Search input tokens | Input-token change | Eager cost | Tool Search cost | Cost change | Eager latency | Tool Search latency | Latency change |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Small | cold/write | 20,023 | 6,184 | −69.1% | $0.082089 | $0.051869 | −36.8% | 11.844 s | 12.598 s | +6.4% |
| Small | warm/read | 20,004 | 6,208 | −69.0% | $0.025667 | $0.025503 | −0.6% | 11.052 s | 12.422 s | +12.4% |
| Medium | cold/write | 20,185 | 6,350 | −68.5% | $0.087990 | $0.058189 | −33.9% | 16.709 s | 13.883 s | −16.9% |
| Medium | warm/read | 20,186 | 6,364 | −68.5% | $0.032375 | $0.030999 | −4.3% | 16.614 s | 15.544 s | −6.4% |

Across both cache phases, Tool Search reduced the total estimated cost by 28.2% for
the small dataset and 25.9% for the medium dataset. Its total measured latency was
9.3% higher for small, but 11.7% lower for medium.

## Result interpretation

### 1. Tool Search substantially reduces the tool-schema context

`programmatic_eager` exposes all 100 function definitions at the beginning of the
request. `programmatic_tool_search` initially defers those definitions and loads five
inventory functions at runtime. This reduced mean input tokens by approximately 69%
in both datasets: from about 20.0K to 6.2K for small and from about 20.2K to 6.4K for
medium.

The token reduction is almost independent of SKU count because it primarily comes
from removing irrelevant tool schemas, not from reducing the number of required
function executions. The medium run still executes the required 30 calls, but it does
not need to place the full 100-function catalog in the model context.

The observed `loaded_tools = 5` should not be read as five executed functions. Tool
Search loaded the five definitions in the relevant inventory namespace, while the
quality gate verified that the three required inventory functions were executed once
for every SKU and that no unrelated namespace was loaded. In other words, the search
was namespace-selective, although it did not narrow the result to only the three
functions ultimately executed.

### 2. The largest cost benefit appears during cold/write

For cold/write runs, Tool Search reduced estimated cost by 36.8% for small and 33.9%
for medium. The main reason is that the stable prefix written by the Tool Search arm
was much smaller: 4,726–4,782 cache-write tokens versus 9,648–9,676 for eager loading.
Because cache-written tokens are charged using a price of 1.25 times the ordinary
input-token price in this experiment, avoiding a large cache write has a material
first-run benefit.

This makes Tool Search especially attractive when requests frequently create new
cache entries, cache keys are fragmented, or traffic does not reliably reuse the same
prefix. In those conditions, an application repeatedly pays the cold/write cost and
cannot depend on later cache reads to amortize the larger eager-loaded catalog.

### 3. Warm/read narrows the cost difference

For warm/read runs, Tool Search reduced cost by only 0.6% for small and 4.3% for
medium, despite retaining the approximately 69% input-token reduction. Eager loading
benefits strongly from prompt caching in this phase: 19,427–19,483 eager input tokens
were cache reads, compared with 4,726–4,782 for Tool Search. The much larger eager
prefix therefore becomes relatively inexpensive once it is served at the cached-input
price.

This does not mean that the token reduction disappeared. It means that raw input-token
count and billed cost are not interchangeable when the token classes have different
prices. The final cost also includes uncached input and output tokens. Since these
saved tables do not include output-token counts, the precise remaining cost difference
cannot be attributed to input categories alone.

The practical implication is that Tool Search's cost advantage depends on cache-hit
behavior. With a highly reusable, stable eager catalog, warm reads can erase most of
the marginal cost penalty of exposing all schemas. Tool Search remains more
context-efficient, but context efficiency does not automatically translate into the
same percentage of cost savings.

### 4. Latency depends on workload size and cannot be inferred from token count alone

For the small dataset, Tool Search was slower: 6.4% in cold/write and 12.4% in
warm/read. Before generating the program, the combined arm must search the catalog and
load the relevant definitions. This hosted processing is on the response's critical
path, even though it is not necessarily a separate client API round trip. With only 9
required function calls, the task is short enough that this mostly fixed search cost
can outweigh the latency benefit of reducing the active tool context from 100
definitions to five.

For the medium dataset, Tool Search was faster: 16.9% in cold/write and 6.4% in
warm/read. The search work remains similar, but the task grows to 30 required function
calls and produces more results for the model to process before the final response.
Against that larger workload, the fixed search cost becomes a smaller fraction of total
time, while carrying roughly 6.4K input tokens instead of 20.2K can matter more during
program generation and follow-up processing. This is the most plausible explanation
for the direction change: Small exposes the fixed search overhead, whereas Medium has
enough downstream work to amortize it and benefit from the smaller context.

The evidence is stronger for medium cold/write than for medium warm/read. Cold/write
improved by 16.9% on the mean and about 14.9% on the median, so the direction is
reasonably consistent across the three runs. Warm/read improved by 6.4% on the mean
but only about 2.8% on the median because one eager run took 20.171 seconds. The result
should therefore remain directional rather than causal: three repetitions cannot
separate context-size effects from model generation, hosted-tool scheduling, and
network variance. More runs with median and p90 reporting are needed before claiming a
general latency advantage or a specific workload crossover point.

### 5. Quality was preserved in this experiment

All 12 runs for each dataset passed the quality gate. Tool Search therefore achieved
its context and cold-cost reductions without reducing correctness in these saved runs.
This matters because lower cost is useful only if the model still loads the required
tools, executes every required SKU/tool combination exactly once, produces the
deterministic program output, and returns the expected final answer.

The result is strong evidence for this controlled inventory scenario, but it does not
establish equivalent recall for ambiguous requests or for catalogs with many
semantically overlapping tools. Those cases need separate tool-selection evaluations.

## Insights and recommended use

1. **Use Programmatic Tool Calling + Tool Search for large, sparsely used catalogs.**
   It is the stronger default when a request needs only one domain or a small subset of
   a much larger catalog. Here it avoided roughly 69% of input tokens while preserving
   quality.

2. **The clearest economic gain is avoiding expensive cold cache writes.** If cache
   reuse is uncertain, Tool Search reduced the measured first-run cost by about one
   third. This is more meaningful than judging the design from warm/read runs alone.

3. **Programmatic Tool Calling without Tool Search can remain competitive for stable,
   frequently reused catalogs.** When the entire tool prefix is reliably cached, its
   warm/read cost approached the Tool Search cost and avoids the additional search
   step. Eager loading may therefore be reasonable when the catalog is small, highly
   stable, and most tools are commonly needed.

4. **Separate context efficiency, monetary cost, and latency.** Tool Search won
   decisively on input-token count in every condition, but its warm-cost advantage was
   modest and its latency direction changed with dataset size. These are distinct
   outcomes and should not be represented by a single efficiency claim.

5. **Measure selection precision in addition to final-answer quality.** The current
   text after this point is not visible in the supplied images.

6. **Extend the benchmark before making a production decision.** Run more repetitions,
   add larger catalogs and the large inventory dataset, retain output and reasoning
   token breakdowns, and test realistic cache-hit ratios. A weighted expected-cost
   calculation across cold/write and warm/read traffic will be more representative
   than either phase in isolation.

## Overall conclusion

For this 100-function inventory benchmark, Programmatic Tool Calling + Tool Search is
the more context-efficient design and provides a clear total-cost advantage, especially
when a cache entry must be written. It also preserved quality across every saved run.
Its latency advantage is workload-dependent rather than universal: the search overhead
was visible for the small task, while the medium task favored Tool Search. Plain
Programmatic Tool Calling remains a credible option when a stable tool catalog receives
very high cache reuse, but Tool Search is the more robust choice when the catalog is
large, only a small subset is relevant per request, or cold-cache traffic is material.
