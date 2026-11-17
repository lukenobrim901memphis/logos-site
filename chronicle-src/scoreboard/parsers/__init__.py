from . import basketball, hockey, football, baseball, soccer

BOX_PARSERS = {
    "basketball": basketball.parse,
    "hockey": hockey.parse,
    "football": football.parse,
    "baseball": baseball.parse,
    "soccer": soccer.parse,
}
