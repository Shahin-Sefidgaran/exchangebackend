from fastapi import Form, HTTPException
from starlette import status

from common.resources import response_strings
from common.resources.account_recovery import questions


async def get_answers_dict(answers: str = Form(...)) -> dict:
    """First validate the answers count then returns dict version of questions and answers
    to use it in admin panel"""
    list_ = answers.split(',')
    answers_dict = {}
    # check answers count be the same as questions
    if len(list_) != len(questions.questions):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=response_strings.WRONG_ANSWERS_COUNT + str(len(questions.questions)))
    for i, ans in enumerate(list_):
        answers_dict[questions.questions[i]] = ans
    return answers_dict
