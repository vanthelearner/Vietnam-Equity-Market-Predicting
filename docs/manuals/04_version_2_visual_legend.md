# Version 2 Visual Legend

## Summary
The documentation uses a small set of repeated diagram patterns.

## Mermaid Node Meanings
| Shape / style | Meaning |
| --- | --- |
| `/path/file.csv/` | a real file artifact |
| `[stage or action]` | a transformation step |
| `[[note]]` | a documentation note |
| arrows | data or control flow |

## Common Flow Patterns
| Pattern | Meaning |
| --- | --- |
| raw file -> stage -> output file | a physical artifact is read and rewritten |
| output file -> model stage | handoff from one pipeline into another |
| predictions -> portfolio -> summary | forecast-to-strategy transformation |
| benchmark + strategy -> active metrics | benchmark-relative evaluation |

## Suggested Reading Rule
When reading a diagram:
1. look for the file nodes first
2. then identify which stage transforms them
3. then read the short table below the diagram
4. only then move to the core code block

## Linked Notes
- [Documentation home](00_version_2_docs_home.md)
- [Process pipeline map](version_2_process_docs/00_version_2_process_pipeline_map.md)
- [Model pipeline map](version_2_model_docs/00_version_2_model_pipeline_map.md)
