# cg_arena


1) javac -d . src/*.java
2) jar cfe cg-mm.jar Referee *.class
3) mettre les params qu'il faut dans arena orchestrator :
   - EXE_DIRECTORY : répertoire de tes exécutables, il en faut un multiple de 3 !
   - REFEREE_JAR : le path vers ton .jar
   - NUMBER_OF_ROUNDS : le nombre de rounds que ca va jouer. Ca peut être 999999, vu que le classement est actualisé à la fin de chaque round sur stdout, t'arrête le programme quand tu veux
   - RANDOM_MATCHING_OFFSET : laisse à 50 ;)
4) Installer les lib jusqu'a ce que l'exécusion de arena orchestrator te crache plus dessus
5) Soit ca marche, soit ca bug


