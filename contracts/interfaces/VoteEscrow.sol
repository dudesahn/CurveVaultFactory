// SPDX-License-Identifier: MIT

pragma solidity ^0.6.12;

interface VoteEscrow {
    function create_lock(uint256, uint256) external;

    function increase_amount(uint256) external;

    function withdraw() external;
}
