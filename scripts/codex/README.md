# Codex batting image generation

This folder preserves the reproducible API workflow for the batting-slide images.
It does **not** claim that an API rerun will reproduce the exact pixels created by
the Codex desktop built-in image tool. Image generation is nondeterministic.

The current unresolved task is to rebuild the two Slide 3 image groups while
keeping the **same athlete used in Slide 2**. The Slide 2 asset is therefore the
first, mandatory reference image for both edit jobs.

## Files

- `generate_batting_images.mjs`: dependency-free Node.js runner for the OpenAI
  Image API.
- `batting-image-jobs.json`: versioned model settings, reference images, prompts,
  output filenames, and the character-consistency rule.
- `docs/drafts/codex/assets/chest-rotation-drill-v2.png`: current canonical
  character and style reference.
- `docs/drafts/codex/assets/hip-mobility-stretch-front-v1.png`: rejected Slide 3
  composition reference. Its movement layout may be reused, but its person must
  not be copied.
- `docs/drafts/codex/assets/right-hitter-left-hip-sequence-v1.png`: rejected
  Slide 3 composition reference under the same rule.

## Requirements

- Node.js 20 or newer. The script uses native `fetch`, `FormData`, `Blob`, and
  `File` support and does not need an npm package.
- `OPENAI_API_KEY` in the environment.
- API access to the model in the manifest.

The manifest pins `gpt-image-2-2026-04-21`. The model supports the image
generation and image edit endpoints. The edit workflow uses the first image as
the identity/style reference and the second image only as the pose/layout
reference. Do not add `input_fidelity`; GPT Image 2 processes image inputs at
high fidelity automatically.

Official documentation:

- https://developers.openai.com/api/docs/models/gpt-image-2
- https://developers.openai.com/api/docs/guides/image-generation

## Usage

```bash
node scripts/codex/generate_batting_images.mjs --list
node scripts/codex/generate_batting_images.mjs \
  --job slide3-mobility-v2 \
  --dry-run
node scripts/codex/generate_batting_images.mjs \
  --job slide3-mobility-v2
node scripts/codex/generate_batting_images.mjs \
  --job slide3-right-hitter-transfer-v2
```

The script refuses to overwrite an existing file unless `--force` is supplied.
Each successful image also gets a sibling `.json` file containing the resolved
job, request ID, model settings, prompt hash, and API usage returned by the
service.

## Mandatory review before using an output

1. The person must match Slide 2 in face treatment, hair, body proportions,
   clothing, and rendering style.
2. Every face must remain blank. No eyes, nose, or mouth.
3. Slide 3 must use a direct front view.
4. In the right-handed sequence, the left stride leg is on the viewer's right.
5. The mobility stretch and batting transfer must remain separate. The former
   moves the waist outside the movement-side foot. The latter stops over the
   left hip and must not use the extreme stretch range.
6. Removing the chair must not shift the weight back to the right.
7. Rotation is around the left hip without locking the left knee.

If any one of these checks fails, do not place the image in the slide. Revise
one point in the prompt at a time and save a new versioned output.
