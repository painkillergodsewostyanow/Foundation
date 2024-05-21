addEventListener("DOMContentLoaded", (event) => {

    const lesson_parts = document.getElementsByClassName('lesson-content')
    const lesson_parts_buttons = document.getElementsByClassName('lesson-part-btn')
    inited = false
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

            if (!inited) {
                editor = CodeMirror.fromTextArea(document.getElementById("editor"), {
                    lineNumbers: true,
                    matchBrackets: true,
                    theme: "ayu-dark",
                });

                console.log(editor)

                select = document.getElementById('lang-lst')
                editor.setOption("mode", select.value);
                
                function chang_lang(){
                    editor.setOption("mode", select.value);
                }

                select.addEventListener('change', chang_lang, false);
                inited = true
            }

        };
    }

    for (var i = 0; i < lesson_parts_buttons.length; i++) {
        lesson_parts_buttons[i].addEventListener('click', createHandler(i));
    }

});