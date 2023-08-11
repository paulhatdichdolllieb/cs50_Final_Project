const submitBtn = document.getElementById('submit');
const password = document.getElementById('password')
const confirmation = document.getElementById('confirmation')
const username = document.getElementById('username')

function updateSubmitBtn() {
    const usernameValue = username.value.trim();
    const password1Value = password.value.trim();
    const password2Value = confirmation.value.trim();
    if (usernameValue && password1Value && password2Value) {
        submitBtn.removeAttribute('disabled');
    } else {
        submitBtn.setAttribute('disabled', 'disabled');
    }
}

username.addEventListener('change', updateSubmitBtn);
password.addEventListener('change', updateSubmitBtn);
confirmation.addEventListener('change', updateSubmitBtn);