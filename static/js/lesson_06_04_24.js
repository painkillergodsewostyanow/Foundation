addEventListener("DOMContentLoaded", (event) => {

    const lesson_parts = document.getElementsByClassName('lesson-content')
    const lesson_parts_buttons = document.getElementsByClassName('lesson-part-btn')

    function createHandler(index) {
        return function() {

            Array.from(lesson_parts_buttons).forEach(el=>{
                el.classList.remove('active')
            })

            Array.from(lesson_parts).forEach(el=>{
                this.classList.add('active')
                el.classList.remove('active')
                lesson_parts[index].classList.add('active')
            })
        };
    }

    for (var i = 0; i < lesson_parts_buttons.length; i++) {
        lesson_parts_buttons[i].addEventListener('click', createHandler(i));
    }
});