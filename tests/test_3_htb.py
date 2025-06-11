from htv import Templater


def test_clean_description():
    description = """Many malicious actors tend to obfuscate their code to avoid it being detected
    by systems or understood by other developers.


    The ability to deobfuscate code is a useful technique that can be applied to various
    real-world scenarios. It is useful on web application assessments to determine if
    a developer has used \"security by obscurity\" to hide JavaScript code containing
    sensitive data. It can also be useful for defenders when, for example, attempting
    to deobfuscate code that was responsible for the Phishing website used in an attack.


    In this module, you will learn the basics of deobfuscating and decoding JavaScript
    code and will have several exercises to practice what you learned.


    You will learn the following topics:


    Locating JavaScript code

    Intro to Code Obfuscation

    How to Deobfuscate JavaScript code

    How to decode encoded messages

    Basic Code Analysis

    Sending basic HTTP requests


    Our final exercise in this module will open a door for many other challenges and
    exercises in Hack The Box!


    Requirements


    It is recommended to take the Web Requests module before this one to get a general
    understanding of how HTTP requests work. If you are already familiar with them,
    then you should be able to start this module.

    Another list:


    step1

    step 2

    step 3


    """
    assert description.count('\n') > Templater.clean_description(description).count('\n')

def test_generate_index():
    p = '/home/redwing/Documents/01-me/vaults/hack-vault'
    print(Templater.generate_index(p))
    assert Templater.generate_index(p)

def test_generate_index_invalid():
    p = '/home/redwing/Documents/01-me/vaults/hack-vault/vpn'
    assert Templater.generate_index(p) is None