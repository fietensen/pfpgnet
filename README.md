# pfpgnet
Python Fast Paced Game Netcode

Communication via TCP and UDP

## This is a work in progress

## Background

Creating a fighting game holds quite some challenges. One of them is the networking. Players
are supposed to see their actions and also those of their opponent at the correct time in order
to correctly react on them. Just exchanging the inputs will be a solution doomed to fail.

Latency is the unavoidable time a player-input takes to arrive at the opponent's game instance.
The higher the latency, the harder it will be for the players to have a pleasant gaming experience.

In order to deal with variable latency, I want to extend the P2P Connection by synchronization as well
as timing functionality so python games can adapt and have an easier time implementing Rollback Netcode.
