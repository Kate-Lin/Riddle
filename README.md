# Riddle
2019.4 RoboCup Riddle Test: Person Memorization &amp; Speech Interaction &amp; Sound Point Localization on robot
This test focuses on human detection, sound localization, speech recognition, and robot interaction with unknown people.
5.4.3. Task
1. Start: The robot starts at a designated starting position and announces it wants to play
riddles.
2. Waiting and turn: After stating that it wants to play a riddle game, the robot waits for
10 seconds while a crowd is merged on it’s back. When the time elapses, the robot must
turn around (about 180°) and find the crowd.
3. Requesting an operator: After turning around, the robot must state the size of the
crowd (including male and female count4) and request for an operator (e.g. who want to
play riddles with me?). The crowd will move and surround the robot, letting the operator
to stand in front of the robot.
4. The riddle game: Standing in front of the robot, the operator will ask 5 questions.
The robot must answer the question without asking confirmation. Questions will only be
asked only once; no repetitions are allowed.
5. [DSPL only] Blind man’s bluff game: Crowd line-up. The crowd will reposition,
lining up in front of the robot. A random person from the crowd standing in front of the
robot will ask a question. The robot may
• Turn towards the person who asked the question and answer the question
• Directly answer the question without turning
• Turn towards the person and ask them to repeat the question
This process is repeated with 10 (possibly) different people. The game will end when the
10th question has been made, following a similar distribution of questions as in the riddle
game. The robot must answer the question without asking confirmation. Questions may
be repeated once.
5. [OPL & SSPL] Blind man’s bluff game: Circling Crowd. The crowd will reposition,
making a circle around the robot. A random person from the crowd surrounding the robot
will ask a question. The robot may
• Turn towards the person who asked the question and answer the question
• Directly answer the question without turning
• Turn towards the person and ask them to repeat the question
This process is repeated with 5 (possibly) different people. The game will end when the
5th question has been made, following the same distribution of questions as in the riddle
game. The robot must answer the question without asking confirmation. Questions may
be repeated once.
6. Leave The robot must leave the arena/test area after all questions have been asked or
when instructed to do so.
