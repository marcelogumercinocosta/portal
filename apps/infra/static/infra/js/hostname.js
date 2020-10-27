///// funcao para corrigir os casmpos que somem do vinculo
function combo_tipo() {
    if ($('#id_tipo').length) {
        if ($('#id_tipo').val() === '') { return;}
        if ($("[data-id]").attr('title') != '---------') {
            $('#id_ip').val($("[data-id]").attr('title'));
        }
    }
}

$(document).ready(function () {
    $('#id_tipo').on('changed.bs.select', function (e, clickedIndex, isSelected, previousValue) {
        if ($('[data-id="id_tipo"]').attr('title') != '---------') {
            let tipo = $('[data-id="id_tipo"]').attr('title').split(" | ")
            $("#id_ip").val(tipo[1] + ".")
        }
    });
    $('#id_ip').mask('999.999.999.999');
});




