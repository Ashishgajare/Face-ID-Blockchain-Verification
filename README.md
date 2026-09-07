TraceFace

Face Identification and Blockchain Verification

TraceFace is an end to end system that takes a face image as input, searches the web for visually similar content, identifies the most likely matching post using face similarity, and records a cryptographic fingerprint on the Ethereum Sepolia blockchain.

The project now includes a Streamlit verification studio with a green and yellow dashboard design. The UI displays the submitted photo, lets the user search for the highest face match, provides links to the matching post and image, and supports anchoring the uploaded-photo record on Sepolia.

The main goal of the project is to demonstrate how face matching, reverse image search, cryptographic hashing, and blockchain verification can work together in a single pipeline.

What TraceFace Does

TraceFace follows this process:

The user provides a face image through the command line pipeline or Streamlit UI.
The system detects the face using InsightFace.
A 512 dimensional face embedding is generated.
The input image is sent to Google Lens through SerpApi for reverse image search.
Google Lens returns visually similar images and web results.
Candidate images are downloaded and their faces are detected.
The faces in the candidate images are compared with the input face using cosine similarity.
The best matching result is selected.
The UI exposes the highest-match post URL and direct image URL.
The discovered record or uploaded-photo fingerprint is converted into a SHA 256 hash.
The hash can be stored on the Ethereum Sepolia blockchain from the UI or CLI flow.
The same information can later be hashed again and compared with the blockchain record.
If the hashes match, the original record has not been modified.
If the hashes are different, the system detects that the data has been changed.

System Architecture

Face Image
     |
     v
Face Detection
     |
     v
Face Embedding
     |
     v
Google Lens Reverse Image Search
     |
     v
Candidate Web Images
     |
     v
Face Similarity Comparison
     |
     v
Best Matching Post
     |
     v
SHA 256 Hash
     |
     v
Ethereum Sepolia Blockchain
     |
     v
Verification
     |
     v
Original Data / Tampered Data

Technologies Used

Python

Used as the main programming language for the entire pipeline.

InsightFace

Used for face detection and generation of face embeddings.

OpenCV

Used for reading and processing images.

NumPy

Used for numerical operations and cosine similarity calculations.

Google Lens through SerpApi

Used to perform genuine reverse image searches and discover matching web content.

SHA 256

Used to create a unique cryptographic fingerprint of the discovered post information.

Solidity

Used to create the TraceFace smart contract.

Ethereum Sepolia

Used as the blockchain network for storing and verifying hashes.

Web3.py

Used to communicate with the Ethereum blockchain from Python.

python dotenv

Used to securely load API keys, blockchain RPC URLs and wallet credentials from environment variables.

Project Structure

traceface/
│
├── app.py
│
├── face/
│   ├── __init__.py
│   ├── detector.py
│   └── matcher.py
│
├── search/
│   ├── __init__.py
│   ├── reverse_search.py
│   └── candidate_matcher.py
│
├── ui/
│   └── app.py
│
├── blockchain/
│   ├── __init__.py
│   ├── blockchain.py
│   ├── deploy.py
│   ├── store_verify.py
│   └── tamper_test.py
│
├── contracts/
│   └── TraceFace.sol
│
├── utils/
│   ├── __init__.py
│   └── hashing.py
│
├── test_images/
│
├── screenshots/
│
├── requirements.txt
│
├── README.md
│
├── .gitignore
│
└── .env

How the Face Matching Works

The input image is first processed using InsightFace.

The system detects the face and generates a 512 dimensional numerical representation called a face embedding.

A face embedding represents important facial features in numerical form. Two images of the same person should generally produce embeddings that are more similar than embeddings belonging to different people.

TraceFace uses cosine similarity to compare the input face with faces found in candidate images.

The similarity score is used together with the ranking of the reverse image search results to select the most relevant candidate.

The project uses a similarity safeguard so that extremely weak matches are not automatically treated as valid matches.

The similarity values demonstrated in this project are intended for the demo pipeline and are not presented as a universal biometric identification threshold.

Reverse Image Search

TraceFace uses Google Lens through the SerpApi API.

The input image is uploaded to the service and Google Lens returns visual matches from the web.

The system then takes the returned candidate images and attempts to download and analyse them.

For each candidate, TraceFace checks whether a face can be detected.

If a face is found, its embedding is compared against the input embedding.

This makes the process dynamic instead of relying on a hardcoded website or predefined result.

Example Discovered Result

During testing, the system successfully discovered a matching image hosted on Unsplash.

The discovered post was:

Title: Women's black top | Free Photo on Unsplash

Source: Unsplash

Post: https://unsplash.com/photos/womens-black-top-25WM4IEnPIg

The detected face similarity for this candidate was approximately 0.9571.

The system therefore selected this result as the best matching candidate for the demonstration.

Cryptographic Verification

Once a matching post is found, TraceFace creates a record containing information about the discovered content.

Title
Source
Post URL

This record is converted into a canonical JSON representation.

SHA 256 is then calculated from this data.

The resulting hash acts as a digital fingerprint of the record.

For the demonstration record, the SHA 256 hash was:

6c443b9fcff709b896531a477f2f6adb1dc7db92aa5096bfdef8518ed42a5588

The important idea is that even a small change to the original information will produce a completely different hash.

Blockchain Verification

The generated SHA 256 hash is stored on the Ethereum Sepolia testnet.

The TraceFace smart contract stores three important pieces of information:

Hash
Timestamp
Submitter wallet address

The contract also provides a verification function that checks whether a particular hash exists on the blockchain.

The deployed contract is:

0x99a70F91bfae2C9ad0ff808eb2465Eb85b8a0a55

The blockchain network used is:

Ethereum Sepolia

Smart Contract

The smart contract contains a mapping between a hash and its blockchain record.

struct Record {
    uint256 timestamp;
    address submitter;
    bool exists;
}

The storeRecord function stores a hash on the blockchain.

The verifyRecord function checks whether the hash exists and returns the timestamp and wallet address associated with it.

An event is also emitted whenever a record is stored.

Streamlit Verification Studio

The Streamlit dashboard is implemented in `ui/app.py`. It provides:

- A green and yellow verification-studio interface.
- Face-image upload and an on-screen preview of the submitted photo.
- A pipeline status rail for detection, embedding, search, matching, hashing and blockchain steps.
- A `Find highest match` action that compares returned candidate faces.
- An `Open Post` link to the highest-scoring source page.
- An `Open Matched Image` link to the candidate image URL.
- Photo SHA-256 and record-hash display.
- An `Anchor on Sepolia` action with the confirmed transaction hash and Etherscan link.

Start the dashboard with:

```bash
python -m streamlit run ui/app.py --server.address 127.0.0.1 --server.port 8502
```

Then open `http://127.0.0.1:8502` in a browser. If that port is already in use, choose another available port.

The UI requires `SERPAPI_API_KEY` for reverse search and `SEPOLIA_RPC_URL` plus `PRIVATE_KEY` for blockchain anchoring. The UI computes the photo fingerprint locally before sending only the hash record to the contract.

Social Media Detection

The `search/social_filter.py` module filters reverse-search results by supported social domains, including Instagram, Facebook, X, Twitter, LinkedIn, YouTube, TikTok and Reddit. It returns the detected platform, source URL, title and image URL so social candidates can be shown alongside the other search results.

Tamper Detection

One of the main purposes of using blockchain in TraceFace is to demonstrate tamper detection.

Suppose the original record is:

Title: Women's black top - Free Photo on Unsplash
Source: Unsplash
Post URL: https://unsplash.com/photos/womens-black-top-25WM4IEnPIg

The system calculates its SHA 256 hash and stores it on the blockchain.

If someone changes the post URL or modifies the title, the system calculates a new hash.

The new hash will not match the hash stored on the blockchain.

During testing, TraceFace produced:

Original SHA 256:
6c443b9fcff709b896531a477f2f6adb1dc7db92aa5096bfdef8518ed42a5588

Tampered SHA 256:
fd898dda3ae0c4ed8dc33fd5bd7bf5bc7914a6e8ae6fbb9a0c12b62fad122083

The blockchain verification showed:

Original hash exists: True
Tampered hash exists: False

TAMPER DETECTED

This demonstrates how the blockchain can be used as an immutable reference for verifying that the discovered information has not been modified.

Example Blockchain Transaction

A successful TraceFace transaction was confirmed on Ethereum Sepolia.

Transaction:
da89af7476c121dce0aa4f0968dad006a890b25633b540b0c9ab0bacd19d8888

Block:
11654418

Gas Used:
31727

The transaction can be viewed on the Sepolia Ethereum block explorer.

View the transaction on Sepolia Etherscan

Environment Setup

Clone the repository and move into the project directory.

git clone <YOUR_GITHUB_REPOSITORY_URL>
cd traceface

Create a Python virtual environment.

python3 -m venv venv

Activate it.

source venv/bin/activate

Install the required dependencies.

pip install -r requirements.txt

Environment Variables

Create a .env file in the project root.

The following variables are required:

SERPAPI_API_KEY=your_serpapi_key
SEPOLIA_RPC_URL=your_sepolia_rpc_url
PRIVATE_KEY=your_wallet_private_key

The .env file is included in .gitignore and should never be uploaded to GitHub.

Never share your private key or API keys publicly.

Running the Project

Activate the virtual environment.

source venv/bin/activate

Then run:

python app.py

The command-line program will run the complete pipeline. For the visual dashboard, run:

python -m streamlit run ui/app.py --server.address 127.0.0.1 --server.port 8502

In the dashboard, upload a face image and select `Run TraceFace`. The submitted photo remains visible in the results area. Select `Find highest match` to compare candidate faces and reveal the source post and matched-image links. Select `Anchor on Sepolia` to hash the uploaded-photo record, submit it to the deployed contract, and verify the stored record.

It will detect the face, perform the reverse image search, analyse candidate images, select the best result, generate the SHA 256 hash, store the hash on the blockchain and verify the record.

Testing Tamper Detection

The tamper detection system can be tested using:

python3 blockchain/tamper_test.py

The script compares the original record against a modified version.

If the information has been changed, the generated hash will be different from the blockchain record and the system will report that tampering has been detected.

Why Blockchain Is Used

A normal database can store information, but its contents can potentially be changed by someone who has access to the database.

TraceFace uses blockchain as an independent verification layer.

The actual image or post does not need to be stored on the blockchain.

Instead, TraceFace stores a cryptographic fingerprint of the discovered information.

This keeps the blockchain record small while still allowing the system to verify whether the information has changed.

Why We Store the Hash Instead of the Image

Storing images directly on a blockchain would be expensive and unnecessary.

Instead, TraceFace stores the SHA 256 hash of the discovered record.

The original information can remain off chain while the blockchain acts as a trusted reference.

Whenever verification is required, the same information can be hashed again and compared with the blockchain value.

Important Design Decisions

TraceFace does not simply assume that the first Google Lens result is the correct person.

The system downloads multiple candidate images and performs an additional face similarity comparison.

This creates an additional verification layer between reverse image search and the final result.

The blockchain also does not determine whether a face belongs to someone.

Its purpose is to verify the integrity of the discovered record after the matching stage.

This separates the identity matching problem from the data integrity problem.

Limitations

Reverse image search results depend on what is publicly indexed on the internet.

Some websites block automated image downloads, which can cause individual candidate images to fail during processing.

Face similarity can also be affected by image quality, lighting, facial angle, occlusion and differences between photographs.

A high similarity score should therefore not be treated as absolute proof of identity.

The current implementation is a hackathon demonstration rather than a production biometric identification system.

Responsible Use

TraceFace should only be used with images and online content that the user is authorized to process.

The project is intended for research, education, verification and controlled demonstrations.

It should not be used to stalk, harass or monitor people without their knowledge or authorization.

The project also avoids permanently storing biometric data on the blockchain.

Only the cryptographic verification record is stored on chain.

Future Improvements

Possible improvements include adding support for more reverse image search providers, improving candidate ranking, adding multiple face detection, supporting video input, improving handling of blocked image hosts and creating a more detailed verification report.

Another possible improvement would be storing additional metadata fingerprints so that changes to the title, source, URL or other selected metadata can be detected independently.

Demo Flow

For the final demonstration, the complete workflow can be shown in the following order:

Input Face Image
        ↓
Face Detection
        ↓
Face Embedding
        ↓
Google Lens Search
        ↓
Candidate Images
        ↓
Face Similarity Matching
        ↓
Best Matching Web Post
        ↓
SHA 256 Hash Generation
        ↓
Ethereum Sepolia Transaction
        ↓
Blockchain Confirmation
        ↓
Hash Verification
        ↓
Tamper Detection Test
