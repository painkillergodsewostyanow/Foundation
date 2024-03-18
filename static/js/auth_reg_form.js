const signInBtn = document.querySelector('.signin-btn');
const signUpBtn = document.querySelector('.signup-btn');
const loginFormToForgotPwdFormTrigger = document.querySelector('.form__forgot')
const forgotPwdFormToLoginFormTrigger = document.querySelector('.form__signin')
const formBox = document.querySelector('.form-box');
const body = document.body;
const loginForm = formBox.getElementsByTagName('form')[0]
const pwdForgotForm = formBox.getElementsByTagName('form')[1]


loginFormToForgotPwdFormTrigger.addEventListener('click', function() {
    loginForm.classList.add('close')
    pwdForgotForm.classList.add('show')
})

forgotPwdFormToLoginFormTrigger.addEventListener('click', function() {
    loginForm.classList.remove('close')
    pwdForgotForm.classList.remove('show')
})


signUpBtn.addEventListener('click', function () {
    formBox.classList.add('active')
    body.classList.add('active')
})

signInBtn.addEventListener('click', function () {
    formBox.classList.remove('active')
    body.classList.remove('active')
})