# Limitations

## Reverse Search Coverage

Google reverse-image search only returns pages that Google indexes and SerpApi can expose. A zero-result response is valid and does not mean the image has never appeared online.

## Private and Deleted Posts

Private, deleted, login-gated, region-blocked, or robots-restricted pages may not appear. Search coverage varies by provider and time.

## API Limitations

SerpApi quotas, rate limits, endpoint changes, temporary-host availability, and network failures can stop a search. The UI reports failure instead of inventing results.

## Inaccessible Images

A result may have a broken thumbnail, an HTML page instead of an image, a blocked CDN, or a file exceeding the configured size limit. Such candidates cannot be compared.

## False Positives and False Negatives

Face similarity is probabilistic. Similar-looking people may score highly, while the same person under difficult conditions may score below the threshold. The result is visual evidence for review, not identity proof.

## Lighting, Pose, and Occlusion

Low light, profile poses, sunglasses, masks, blur, compression, cropping, and occlusion can reduce detection or embedding quality.

## Similarity Threshold

The production threshold is `0.65`. It is a project configuration, not a universal biometric standard. Changing it changes the review policy and should be justified with validation data.

## Blockchain Gas

Polygon transactions require test POL on Amoy. Gas prices and minimum tip caps can change. RPC providers can be unavailable or rate-limited.

## Testnet Limitations

Polygon Amoy is a testnet. Its assets have no production value, data availability is not a production SLA, and deployment addresses differ from mainnet.

## Privacy and Retention

Reverse search requires the image to be made available to an external search service through a temporary public URL. Do not use sensitive images without consent. The contract stores public URLs and hashes permanently on-chain, so do not put private data in those fields.
