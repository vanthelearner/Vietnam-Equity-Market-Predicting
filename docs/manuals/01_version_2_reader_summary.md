# Version 2 Reader Summary

## Summary
`version_2` is a two-stage research pipeline:
- `/process` cleans and engineers a broad daily stock and macro panel
- `/model` converts that broad daily panel into a monthly prediction panel, then runs rolling models and portfolio evaluation

## What Changed Relative to the Older Design
- liquidity control moved out of `/process` and into `/model`
- daily return and target construction is calendar-step based rather than next-observed-row based
- `/model` now owns benchmark construction and monthly panel preparation
- the modeling feature set is curated instead of carrying every numeric field forward

## What the Reader Should Understand First
1. `/process` does not choose the final trading universe.
2. `/model` does not start from raw Bloomberg-style data.
3. the handoff file is `/process/outputs/03_model_data/daily_model_data.csv`.
4. the core monthly file is `/model/data/panel_input.csv`.

## Quick Architecture
| Layer | Main file | Output |
| --- | --- | --- |
| daily stock engineering | `/process/src/v2_process/stages/transform_stock.py` | transformed stock panel |
| daily stock cleaning | `/process/src/v2_process/stages/process_stock.py` | `clean_stock_daily.csv` |
| daily stock + macro merge | `/process/src/v2_process/stages/build_model_data.py` | `daily_model_data.csv` |
| monthly panel build | `/model/src/v2_model/prepare_inputs.py` | `panel_input.csv` |
| monthly filtering and scaling | `/model/src/v2_model/preprocess.py` | `PreparedData` |
| rolling model loop | `/model/src/v2_model/pipeline.py` | run outputs |

## Best Reading Order
- [Worked example](03_version_2_end_to_end_worked_example.md)
- [Process pipeline map](version_2_process_docs/00_version_2_process_pipeline_map.md)
- [Model pipeline map](version_2_model_docs/00_version_2_model_pipeline_map.md)
- [Process stock stage](version_2_process_docs/13_src_v2_process_stages_process_stock.md)
- [Monthly input preparation](version_2_model_docs/11_src_v2_model_prepare_inputs.md)
- [Monthly preprocessing](version_2_model_docs/12_src_v2_model_preprocess.md)
- [Model orchestration](version_2_model_docs/17_src_v2_model_pipeline.md)

