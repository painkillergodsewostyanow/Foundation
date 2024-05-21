$(document).ready(function() {
    $('#editor_form').on('submit', function(event) {
        event.preventDefault();

        data = {"editor": editor.getValue()}
        console.log(data)

        $.ajax({
            url: $(this).attr('action'),
            type: 'POST',
            dataType: 'json',
            data: data,
            headers: {
              'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').val()
            },
            success: function(data) {
                success(data)
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.error('Error submitting form:', textStatus, errorThrown);
            }

        });
    });
});



function success(data){
    result_block = editor_form = document.getElementById('result_block')
    result_block.innerText = ""

    if (data.status){
        div = document.createElement("div");
        div.innerText = "Решено!"
        div.style.color = 'green'

        barge = document.getElementById(`solved_${data.code_task_pk}`)
        barge.textContent = "Решено"

    }
    else{
        div = document.createElement("div");
        div.innerText = "Не верно"
        div.style.color = 'red'
    }
    result_block.append(div)
    if (data.output){
        result_block.append(data.output)
    }

}


