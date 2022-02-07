expr : identifier | number ;

parameter_list : ( expr ( "," expr )* )? ;

function_call : identifier "(" parameter_list ")" ;

if_stat : "if" "(" expr ")" stat else_section ;

else_section : ( "else" stat )? ;

stat : expr ";" | if_stat ;
