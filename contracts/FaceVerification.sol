// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract FaceVerification {
    struct Verification {
        bytes32 recordHash;
        string postUrl;
        string platform;
        uint256 timestamp;
        bool exists;
    }

    mapping(bytes32 => Verification) private verifications;

    event VerificationStored(
        bytes32 indexed recordHash,
        string postUrl,
        string platform,
        uint256 timestamp,
        address indexed submitter
    );

    function storeVerification(
        bytes32 recordHash,
        string calldata postUrl,
        string calldata platform
    ) external {
        require(recordHash != bytes32(0), "empty record hash");
        require(!verifications[recordHash].exists, "record already exists");

        verifications[recordHash] = Verification({
            recordHash: recordHash,
            postUrl: postUrl,
            platform: platform,
            timestamp: block.timestamp,
            exists: true
        });

        emit VerificationStored(
            recordHash,
            postUrl,
            platform,
            block.timestamp,
            msg.sender
        );
    }

    function getVerification(bytes32 recordHash)
        external
        view
        returns (
            bytes32 storedHash,
            string memory postUrl,
            string memory platform,
            uint256 timestamp,
            bool exists
        )
    {
        Verification memory verification = verifications[recordHash];
        return (
            verification.recordHash,
            verification.postUrl,
            verification.platform,
            verification.timestamp,
            verification.exists
        );
    }
}
