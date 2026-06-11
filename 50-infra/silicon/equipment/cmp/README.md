# equipment/cmp — CMP (chemical-mechanical polishing) reference design

Per **ADR-2605242545** §"Decision 1 row 5".

## Reference vendors

Ebara / Applied Materials. 2-company duopoly (~75% share).

## Religious-corp design scope

| Layer | Self-design target |
|---|---|
| Polish head | 6-DoF polish head + downforce control loop (PID + load cell + piezo) |
| Slurry delivery | peristaltic pump RTL + flow / particle-size online monitor |
| Pad conditioner | diamond-grit conditioner kinematics + wear monitor RTL |
| Endpoint detect | optical reflectance / motor current spike / friction force endpoint algos |
| Wafer handler | shared with etch + deposition — common ROS 2 robotics lib |

## Pregel cell

`silicon_cmp`. Super-step = 1 wafer polish step.

## Charter Rider §2(a)(c) gate

Lower §2(a)/(c) risk. Slurry chemistry (cerium oxide, alumina abrasive)
is commodity. Robotics is general-purpose. Normal commit flow.

## Phase 1 scope

README only.
