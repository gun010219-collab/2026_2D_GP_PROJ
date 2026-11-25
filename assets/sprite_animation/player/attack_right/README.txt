CHECKMATE R7-A3E-2 / Right attack prototype

frames/: 8 independently extracted, normalized 384x384 RGBA poses.
player_attack_right_8frames.png: unpadded 4x2 review/authoring sheet (not runtime atlas).
reference_idle_384.png: original 256x256 sprite embedded at (64,64), for scale reference only.
handoff.json: handoff metadata, not the existing game manifest. Use the actual build_sprite_atlas.py schema.
Anchor top-left coordinate (192,302); match original 256px sprite scale.
Immediate attack playback starts with 05_release; first four frames are authoring poses, not an input delay.
Use existing runtime atlas padding, clip validation and mesh fallback.
Generated art is AI-assisted; source provenance is retained in metadata.
