# Three-round iterative review

In the exploration of factory patterns and functionalities in the second research question, the process involves manual assessment, where individual subjectivity may impact the effectiveness of the study. To mitigate this, we employed a three-round iterative auditing method, with each round involving group discussions among contract experts. Here are summaries of our audit records for each round.

## Round1

### Functionalities

Functionalities refer to the low-level code implementation of factory contracts. Review can be initiated from several perspectives:

1. Identification of basic components of a functionality within Solidity contracts (consulting the Solidity official documentation).
2. Presenting various implementations for a functionality.
3. Providing real-world examples of Ethereum smart contract implementations for each approach.

### Patterns

Patterns encompass high-level features composed of combinations of low-level functionalities.

It involves not only the factory itself but also scrutiny of contracts created and deployed by it. (For example, the metamorphosis contract pattern emerges from interactions between the factory and the deployed contract.)

## Round2

### Functionalities

Issue: Many functionalities appear similar but differ in implementation.

Response: Classify them into coarse-grained categories based on behavior, such as Validity Check and Contract Deployment, then further subdivide them into finer-grained sub-functionalities. For example, under Contract Deployment, sub-functionalities include specific deployment methods (create/create2) and deployment time selection.

### Patterns

While functionalities focus on syntactic features, patterns also involve semantic features, bridging RQ2-RQ3 to explain the rationale and primary usage of each pattern, establishing causal relationships.

## Round3

### Functionalities

1. Merged Tracking and Maintenance into a single functionality.
2. Validity Check not only involves verifying contract addresses but also includes validating contract configurations for template-based contracts, such as the `_validateConfig` method of 0x57e037f4d2c8bea011ad8a9a5af4aaeed508650f.

### Patterns

Introduced the create3factory pattern, where the deployed contract address is determined solely by the salt and deployer address. Unlike singleton factories, which only deploy contracts with identical bytecode to the same address across different chains.
