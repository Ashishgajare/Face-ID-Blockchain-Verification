// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract TraceFace {

    struct Record {
        uint256 timestamp;
        address submitter;
        bool exists;
    }

    mapping(bytes32 => Record) private records;

    event RecordStored(
        bytes32 indexed hash,
        uint256 timestamp,
        address indexed submitter
    );

    function storeRecord(bytes32 hash) public {
        records[hash] = Record({
            timestamp: block.timestamp,
            submitter: msg.sender,
            exists: true
        });

        emit RecordStored(
            hash,
            block.timestamp,
            msg.sender
        );
    }

    function verifyRecord(bytes32 hash)
        public
        view
        returns (
            bool exists,
            uint256 timestamp,
            address submitter
        )
    {
        Record memory record = records[hash];

        return (
            record.exists,
            record.timestamp,
            record.submitter
        );
    }
}