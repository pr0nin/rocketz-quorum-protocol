## Line of sight weapons 

> Specifically line of sight with infinite range?

In the context of the Rocketz Quorum Protocol (RQP), "infinite range" for a line-of-sight weapon changes the calculation from a fixed-point interpolation between two known points to a **ray-casting algorithm** that iterates until it hits a termination condition.
Because RQP must remain deterministic and performant for the quorum to reach consensus, "infinite" is technically defined as "until the edge of the active simulation" or "until an obstruction is met."
### 1. The Directional Vector
Instead of calculating distance N between a start and end hex, an infinite weapon uses an **Origin** (q, r, s) and a **Direction Vector**. In a hex grid, there are six primary directions:
 * (+1, -1, 0), (+1, 0, -1), (0, +1, -1), (-1, +1, 0), (-1, 0, +1), (0, -1, +1).
### 2. The Iterative Step Logic
The protocol calculates the path by repeatedly adding the direction vector to the current hex coordinates.
**The Algorithm Loop:**
 1. **Start:** Set current_hex = origin_hex.
 2. **Check Condition:**
   * **Is current_hex outside the Map Boundary?** (If yes, Terminate).
   * **Does current_hex contain an Opaque Obstacle?** (If yes, Hit and Terminate).
   * **Does current_hex contain a Target?** (If yes, Hit and Terminate/Continue depending on weapon "piercing" rules).
 3. **Step:** Add direction_vector to current_hex.
 4. **Repeat.**
### 3. Handling Diagonal "Off-Axis" Fire
If the weapon is not fired exactly in one of the six primary directions (i.e., it is aimed at a specific coordinate further away), the protocol uses the **Fixed-Point Lerp** logic but sets the "Target" point far beyond the grid's edge.
To keep this deterministic, the RQP engine uses a **Max Grid Constant**. For example, if the active play area is 100 hexes wide, the engine might calculate the line as if the target were at a distance of 1,000 hexes. This ensures the line remains perfectly straight across the entire visible board without needing complex floating-point trigonometry.
### 4. Deterministic Collision in the Quorum
The most critical part for your agent is understanding the **Ordering of Events**:
 * **Simultaneous Resolution:** RQP processes all moves in a "tick." If an infinite weapon is fired, the LOS is calculated against the *final revealed positions* of all agents for that tick.
 * **Fuel as a Limit:** While the *range* is infinite, the *cost* to fire may be fixed. However, some RQP variants tax infinite weapons based on the number of hexes the "ray" actually traverses before hitting a target or the boundary.
### 5. Tactical Implications for Your Agent
When coding your agent's strategy for infinite range weapons:
 * **The "Corridor" Control:** Your agent can effectively "lock down" an entire row of hexes. By checking the direction vector, you can calculate every hex that will be affected and use that as a "No-Go Zone" in your pathfinding.
 * **Back-Tracing:** You can calculate the inverse. If you know where an enemy is, you can calculate the six "infinite lines" that intersect their position to determine where you must stand to hit them from a distance.
This allows your agent to maintain a "Sniper" profile, staying on the edge of the map and firing across the entire board while minimizing its own movement (and thus, fuel consumption).


## Potential weapon types 

> Ok, so there is an opening for a "thick" or cone shaped beam weapon with shorter range in rqp as an addition?

There is a significant tactical and technical opening for "thick" or cone-shaped weapons within the RQP framework. While the protocol currently defaults to "thin-line" logic for performance and deterministic simplicity, a wider-area weapon provides a necessary counter-play to the precision-dodging that high-level agents use.
Here is how those mechanics would be structured to remain compliant with the RQP consensus model:
### 1. The "Thick" Beam (Super-Cover)
Instead of a single-file line of hexes, a "thick" beam uses **Super-Cover** logic. This ensures that if a line so much as "scrapes" the edge of a hex, that hex is included in the damage calculation.
 * **Deterministic Calculation:** Instead of sampling at N intervals (where N is distance), the algorithm samples at 2N or 3N. Any hex index generated during this higher-frequency sampling is added to the "hit set."
 * **Tactical Use:** This eliminates the "Vertex Miss" discussed earlier. It makes certain corridors impossible to traverse without taking damage, forcing opponents to use more fuel to take longer routes.
### 2. The Cone (Sector-Based)
A cone-shaped weapon (like a short-range pulse or shrapnel blast) shifts the logic from linear interpolation to **Coordinate Range** checks.
 * **The Algorithm:** A cone is defined by an **Origin**, a **Direction**, and an **Arc Angle**.
   1. The engine identifies all hexes within a certain distance R (e.g., 3 hexes).
   2. For each hex in that radius, it calculates the angle relative to the origin.
   3. If the angle falls within the weapon's defined arc, the hex is hit.
 * **Fixed-Point Constraints:** To keep this deterministic, RQP would likely use a pre-calculated "Look-up Table" (LUT) for angles on a hex grid. This avoids calling atan2 or other non-deterministic floating-point trigonometric functions during the quorum's validation phase.
### 3. Balancing the "Short-Range" Trade-off
In a fuel-constrained environment like RQP, these weapons fill a specific niche:
 * **Fuel Efficiency vs. Accuracy:** A "thin" infinite sniper is high-precision but easy to dodge. A "thick" short-range blast is almost impossible to dodge but requires the agent to spend fuel closing the distance.
 * **Zoning:** These weapons are perfect for "Economic Warfare." An agent can fire a cone to cover a group of hexes near a high-value objective, essentially "taxing" any opponent who tries to claim it.
### 4. Deterministic Collision Resolution
The biggest hurdle for adding these to the RFC is the **Computational Weight**. Checking 1 hex for a sniper shot is fast. Checking 12 hexes for a cone blast is 12x slower.
To maintain the protocol's speed, the "thick" weapon's hit-set is usually calculated **once** by the firing agent and sent as part of the "Reveal" data. The Quorum then simply verifies that the provided list of hexes matches the protocol's deterministic rules, rather than re-calculating the entire area from scratch.

> Yes, would it be feasable to have a way of knowing how many steps a long range (thick or thing) weapon should be verified by the quorum each round based on dynamic shapes using a relevant target list to generate said outer edges of relevance - then only the shooter would calculate to VERY LONG DISTANCE and the rest would check each step until the dynamic limit, and then return early - the full calculations would have to be done by all post game as part of verifying the validity of the game

This is a highly feasible and computationally elegant approach to scaling RQP. You are essentially proposing a **Two-Tier Verification System** that separates **Real-Time Consensus** (keeping the game moving) from **Post-Game Auditing** (ensuring absolute integrity).
By using a "Dynamic Relevance Limit," the quorum avoids doing "infinite" work on every tick while still maintaining a trustless environment.
### 1. The Real-Time Layer: "Quorum Pruning"
Instead of the quorum calculating a ray to the edge of the universe, the protocol uses a **Bounding Box of Relevance**.
 * **Target List Generation:** At the start of the "Reveal" phase, all agents' positions are known. The protocol generates a list of "Active Entities."
 * **The Dynamic Limit:** The quorum calculates the distance to the *furthest* active entity along the weapon's trajectory.
 * **The Pruned Check:** The quorum nodes only run the deterministic stepping algorithm until they pass that furthest entity. Once they reach that coordinate plus a small buffer (to account for potential obstacles), they **Early Return**.
### 2. The Shooter’s Burden: "Proof of Trajectory"
To make this work, the shooter doesn't just say "I fire North." They provide a **Claimed Trajectory Hash**.
 * The shooter calculates the full path (even to infinite distance).
 * They commit to the full path in their "Reveal" packet.
 * The quorum only checks the segment that actually interacts with the current game state. If the quorum finds a hit within the "Active Zone," the damage is applied.
### 3. The Post-Game Layer: "Deep Audit"
The "infinite" part of the weapon only matters if it affects something. Since the quorum already verified all interactions with ships/objects in the active zone, the game remains consistent.
However, to prevent "Protocol Griefing" (where a shooter claims a path that is mathematically impossible but only revealed as such in the far distance), the **Post-Game Audit** comes into play:
 * Once the match ends, the full ledger is available.
 * Aggregated nodes (or "Archive Nodes") run the full, unpruned calculation for every shot fired.
 * If a discrepancy is found—even 1,000 hexes away—the shooter’s "Protocol Reputation" or staked fuel could be slashed retroactively.
### 4. Handling "Thick" or "Cone" Shapes
For dynamic shapes like cones or thick beams, the "Outer Edges of Relevance" are even more valuable:
 * **Geometric Bounding:** The quorum defines a "Circular Sector" (the cone) that encompasses all possible hit-hexes.
 * **AABB (Axis-Aligned Bounding Box) Check:** Before doing any hex-by-hex math, the quorum checks if any ship's q, r coordinates fall within the broad bounding box of the cone.
 * **Early Exit:** If no ships are in the box, the quorum skips the expensive trigonometric/LUT math entirely for that weapon that round.
### Why this fits the RQP Pitch:
This "Dynamic Pruning" strategy is a massive selling point for your agent pitch. It shows that your team isn't just thinking about **strategy**, but also about **protocol scalability**.
**The Argument:** "Our agent supports high-compute weapon types (Cones/Thick Beams) because we've engineered a Pruned Verification Logic. We minimize Quorum CPU load by only calculating 'Impact Zones' during the match, deferring the 'Infinite Verification' to the post-game audit. This allows for complex combat without slowing down consensus."

> I wonder if this could be used to create a sort of hidden, high cost to discover by opponents, mechanism.
>
> Let's say a fuel farming system where using a low quality weapon to "mine" for fuel, in a way that is obfuscated "real time" but can be verified post-game.
> 
> Say the agent has to shoot and hit a specific target 1000 or even 10000 hexes out - if the weapon hits something in between in its a failure, but if the shot passes the target N fuel can be added (and signed by the shot) instantly.
> 
> If another agent is hit by the shot it damages as usual and a clever agent could calculate seemingly real shots that just misses and as a gambit actually gives them fuel instead ie. win-win, but time expensive to find

This is a brilliant application of **"Zero-Knowledge Strategy"** within a deterministic protocol. You are essentially proposing a way to turn the **computational cost of verification** into a strategic fog of war.
In RQP, where every action is a transaction, this creates a "Proof-of-Work" style mining mechanic embedded directly into combat maneuvers. Here is how that "Deep-Space Fuel Mining" (DSFM) mechanism would function and why it’s so strategically "expensive" for opponents to counter.
### 1. The "Long-Range Proof" (LRP)
The agent fires a "Low-Yield, Long-Range Scan" (the mining shot).
 * **The Condition:** The shot must travel exactly D distance (e.g., 10,000 hexes) without intersecting any object.
 * **The Mining Reward:** If the line is clear, the protocol grants the agent N fuel.
 * **The Instant Validation:** Because the Quorum uses the "Dynamic Pruning" we discussed, they only check the first 100 hexes (the active bubble). If it's clear there, they sign off on the block. The agent gets the fuel *now* based on the assumption that the rest of the 9,900 hexes are empty.
### 2. The Gambler’s Obfuscation
This creates a fascinating psychological game for opponents:
 * **The "Fake" Attack:** You fire a shot directly at an enemy. They see the trajectory and spend fuel to dodge.
 * **The Reality:** You actually *wanted* them to dodge. By moving out of the way, they cleared the "Active Zone" for your shot, allowing it to reach the 10,000-hex mark and "mine" fuel.
 * **The Hidden Win:** You didn't just miss; you effectively traded a low-cost shot for a high-value fuel payout, and your opponent paid fuel to help you achieve it.
### 3. The Verification Tax (Cost to Discover)
If an opponent suspects you are "mining," they face a massive computational hurdle to prove it:
 1. **Passive Ignore:** They can ignore your "misses," but you'll slowly outpace them in fuel.
 2. **Active Audit:** To prove you are mining, they must run the full 10,000-hex calculation in real-time on their own client.
 3. **The Sabotage:** A clever opponent won't just audit you; they will move an object (like a drone or themselves) into the path at hex 5,000. Because the shot is "all or nothing," hitting an object halfway through the "infinite" path turns the fuel gain into a fuel *loss* (the cost of the shot with zero reward).
### 4. Post-Game Slashing: The "integrity Check"
If an agent tries to cheat by mining a path that *does* have an obstacle 5,000 hexes out, the Quorum won't catch it during the live match because of the Pruning Limit.
 * **The Audit:** Post-game, the "Deep Audit" nodes run the full line.
 * **The Penalty:** If they find that the "Mining Shot" actually hit a rogue asteroid at hex 4,500, the agent is retroactively disqualified, and their wins are stripped. This ensures that agents only "mine" if they are 100% certain the path is clear.
### Why this is a "Killer Feature" for your Pitch:
In a hackathon, judges love mechanisms that create **Asymmetric Information**.
> "Our agent doesn't just fight; it performs **Computational Obfuscation**. We utilize the RQP Pruning Limit to hide long-range fuel-harvesting shots behind standard combat maneuvers. To stop our fuel growth, opponents must either spend their own CPU cycles auditing the 'void' or spend fuel to physically block paths they only *suspect* are being mined. We turn the protocol's efficiency into our tactical advantage."
> 
### The "Mine-or-Miss" Logic Table

| Opponent Action | Your Shot is a Combat Hit | Your Shot is a Mining Success |
| :--- | :--- | :--- |
| **Doesn't Move** | Opponent takes damage; You lose shot cost. | Shot is blocked; You lose shot cost. |
| **Dodges** | Opponent spends fuel; You lose shot cost. | Path is cleared; **You gain N Fuel.** |

This creates a "Damned if you do, Damned if you don't" scenario for the rival agent—the hallmark of a winning hackathon project.