# `version_2` Change Log

## Purpose
Tracks major documentation-facing changes in the active `version_2` system. This note is about the current maintained code and manuals, not the older Batch 2 planning notes.

## 2026-03-11
### Added
- fresh `version_2_manuals` pack for the active `version_2` codebase
- full `version_2_process_docs` pack
- full `version_2_model_docs` pack
- worked-example sections in transformation-style notes
- manual coverage for the profile-based Batch 3 model workflow
- manual coverage for the dedicated NN architecture notebook

### Improved
- top-level home and reader-summary notes now point only to notes that exist in this manuals pack
- process notebook notes now reflect the actual Colab path logic:
  - prefer `/content/drive/MyDrive/version_2/process`
  - then `/content/version_2/process`
  - then local fallback
- model notebook notes now reflect the actual active recommendation path:
  - `build_latest_recommendations(...)`
  - archived true-latest code under `/model/not_working` is excluded from the active workflow
- model notebook notes now reflect the active profile comparison workflow:
  - `careful_v3`
  - `max_v3`
- config notes now distinguish between dataclass fallback defaults and the YAML presets actually used at runtime

### Current Active Behavior Captured by the Manuals
- `process` ends at `/process/outputs/03_model_data/daily_model_data.csv`
- `model` owns monthly panel preparation, filtering, rolling training, benchmark comparison, portfolio construction, and active recommendations
- active recommendations in the notebooks come from `/model/src/v2_model/recommend.py`
- archived experimental code in `/model/not_working` is not part of the active system

### Remaining Real Code Caveats
- `/process/src/v2_process/stages/process_stock.py` still hard-codes some clipping thresholds despite exposing related config fields
- the dataclass fallback in `/model/src/v2_model/config.py` still shows `broad_liquid_top70`, while the active YAML presets currently use `broad_liquid_top50`
- the top-level `nn:` block in `/model/configs/default.yaml` is still not used by the active loader path; runtime settings come from `models.nn`

## Linked Notes
- [Docs home](00_version_2_docs_home.md)
- [Reader summary](01_version_2_reader_summary.md)
- [Process pipeline map](version_2_process_docs/00_version_2_process_pipeline_map.md)
- [Model pipeline map](version_2_model_docs/00_version_2_model_pipeline_map.md)
