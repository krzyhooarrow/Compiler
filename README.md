# Compiler

![Build Status](https://travis-ci.org/joemccann/dillinger.svg?branch=master) ![cov](https://camo.githubusercontent.com/80c8e0138ba434cfdc9d0708c55302d293be60a2/68747470733a2f2f636f766572616c6c732e696f2f7265706f732f6769746875622f5061696e7465725175626974732f556e697466756c2e6a6c2f62616467652e7376673f6272616e63683d6d6173746572) ![docs](https://camo.githubusercontent.com/f7b92a177c912c1cc007fc9b40f17ff3ee3bb414/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f646f63732d737461626c652d626c75652e737667)

Compiler project for computer security 5 sem. Transforms code 
from specified language to delivered wirtual machine language (desc below).

> A compiler is a special program that processes statements written 
> in a particular programming language and turns them into machine 
> language or "code" that a computer's processor uses. 
> Typically, a programmer writes language statements in a language 
> such as Pascal or C one line at a time using an editor.


### Language
- ![](https://placehold.it/15/f03c15/000000?text=+) `program -> DECLARE declarations   BEGIN commands END 
 | BEGIN commands END`
- ![](https://placehold.it/15/c5f015/000000?text=+) `declarations -> declarations , pidentifier
 | declarations , pidentifier (num :num )
 | pidentifier
 | pidentifier (num :num )`
- ![](https://placehold.it/15/1589F0/000000?text=+) `commands -> commands command
 | command`
- ![#](https://placehold.it/15/c5a015/000000?text=+) `command -> identifier ASSIGN expression ;
 | IF condition THEN commands ELSE commands ENDIF
 | IF condition THEN commands ENDIF
 | WHILE condition DO commands ENDWHILE
 | DO commands WHILE condition ENDDO
 | FOR pidentifier FROM value TO value DO commands ENDFOR
 | FOR pidentifier FROM value DOWNTO value DO commands ENDFOR
 | READ identifier ;
 | WRITE value ;`

-  ![#](https://placehold.it/15/efe015/000000?text=+) `expression -> value
 | value PLUS value
 | value MINUS value
 | value TIMES value
 | value DIV value
 | value MOD value`
- ![#](https://placehold.it/15/000/000000?text=+) `condition -> value EQ value
 | value NEQ value
 | value LE value
 | value GE value
 | value LEQ value
 | value GEQ value`
- ![#](https://placehold.it/15//000000?text=+) `value -> num
 | identifier`
- ![#](https://placehold.it/15/c5ffff/000000?text=+) `identifier -> pidentifier
 | pidentifier ( pidentifier )
 | pidentifier (num )`


### Program example
Prints value converted to binary.


```diff
1 DECLARE
2 a, b
3 BEGIN
4 READ a;
5 IF a GEQ 0 THEN
6 WHILE a GE 0 DO
7 b ASSIGN a DIV 2;
8 b ASSIGN 2 TIMES b;
9 IF a GE b THEN
10 WRITE 1;
11 ELSE
12 WRITE 0;
13 ENDIF
14 a ASSIGN a DIV 2;
15 ENDWHILE
16 ENDIF
17 END
```


### Writual-machine

Machine consists of memory cells ***p[i]*** labeled as _0,1,2..._ up to _2^62_ and orders counter ***k***. 
Machine performs step by step each order starting from 0. 
Comments are allowed, starts from ***#*** and are valid to the end of line.
Table below contains possible orders, their interpretation and cost . 

| ***COMMAND*** | ***INTERPRETATION*** |***COST***|
| ------ | ------ | ------ |
| ***GET***  | get value from std input and stores it at _p[0]_.  _k++_ |***100***|
| ***PUT*** | display value at std output from _p[0]_. _k++_ |***100***|
| ***LOAD i*** | _p[0]_ = _p[i]_ and _k++_|***10***|
| ***STORE i*** |  _p[i]_ = _p[0]_ and _k++_ |***10***|
| ***LOADI i*** |  _p[0]_ = _p[p[i]]_ and _k++_|***20***|
| ***STOREI i*** |  _p[p[i]]_ = _p[0]_ and _k++_|***20***|
| ***ADD i*** |  _p[0]_ = _p[0]_+ _p[i]_ and _k++_ |***10***|
| ***SUB i*** |  _p[0]_ =  _p[0]_-_p[i]_ and _k++_ |***10***|
| ***SHIFT i*** | _p[0]_ = 2^ _p[i]_ * _p[0]_ and _k++_ |***5***|
| ***INC*** |  _p[0]_ = _p[0]_+1 and _k++_ |***1***|
| ***DEC*** |  _p[0]_ = _p[0]_-1 and _k++_ |***1***|
| ***JUMP j*** |  _k_ = _j_ |***1***|
| ***JPOS j*** |  if ( _p[0]_ > 0 ) then {_k_ = _j_} else {_k++_}  |***1***|
| ***JZERO j*** |  if ( _p[0]_ = 0 ) then {_k_ = _j_} else {_k++_}  |***1***|
| ***JNEG j*** |  if ( _p[0]_ < 0 ) then {_k_ = _j_} else {_k++_}  |***1***|
| ***HALT*** |  Ends program |***0***|


### Installation

Compiler requires  python 3 to run.

```sh
$ sudo apt update
$ sudo apt install python3
$ sudo apt install python3-pip
$ pip3 install ply
```

Usage:

```sh
$ python3 Compiler.py ${input_file} ${output_file}
```


