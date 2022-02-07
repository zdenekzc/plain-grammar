
while_stat :  "while" "(" expr ")" stat ;

if_stat    :  "if" "(" expr ")" stat ( "else" stat  )? ;

compound_stat : "{" ( stat )* "}" ;

simple_stat :  expr ";" ;

empty_stat :  ";" ;

stat : while_stat | if_stat | compound_stat | simple_stat | empty_stat ;



simple_expr : identifier | number  | "(" expr ")" ;

mult_expr : simple_expr ( ("*"|"/") simple_expr )* ;

add_expr : mult_expr ( ("+"|"-") mult_expr )* ;

expr : add_expr ( "=" expr )? ;



program : stat;


