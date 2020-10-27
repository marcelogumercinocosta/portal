//colorir as tds do rack e setar seus valores no input



function rack_color() {
    let posicoes = [];
    let linhas = [];
    $("#datacenter_body").on("click", "td", function(){
        if(posicoes.length >= 4) {
            posicoes = [];
            $("#show_field").html('');
            $("td").removeClass("blue lighten-4");
        }

        if(linhas.length === 0) $("#show_field").html('');
        if(linhas.length === 1) $("#show_field").html('');
        let classe = $(this).attr('class').split(/[\s_]+/);
        let coluna = parseInt(classe[1]);
        let index = parseInt(classe[3]);
        posicoes.push(coluna, index);

        let th = $(this).parent().find("th.linha").attr('id');
        linhas.push(th);

        $("#id_posicao_linha_inicial").val(linhas[0]);
        $("#id_posicao_linha_final").val(linhas[1]);
        $("#show_field").append(linhas[0],posicoes[0]);
        
        if(posicoes.length === 4) {
            $("#show_field").append(`  (${linhas[0]}${posicoes[0]} - ${linhas[1]}${posicoes[2]})`);
        }

        if(linhas.length >= 2) linhas = [];

        if($(this).children("div").length === 0) {
            
            $("td").removeClass("green lighten-4");
            $(this).addClass("blue lighten-4");
            for(var i = Math.min(posicoes[0], posicoes[2]); i <= Math.max(posicoes[0], posicoes[2]); i++) {
                for(var j= Math.min(posicoes[1], posicoes[3]); j <= Math.max(posicoes[1], posicoes[3]); j++) {
                    let tdcolor = $("td.index_" +j+ ".col_" +i);
                    tdcolor.addClass("blue lighten-4");
                }
            }
        } else {
            alert("Cadastre o rack em um espaço vazio!");
            posicoes = [];
            linhas = [];
            $("#show_field").html('');
            $("td").removeClass("blue.lighten-4");
        }
        if(posicoes.length === 4) {
            $("#selected-fields").show();
            $("#id_posicao_coluna_inicial").val(posicoes[0]);
            $("#id_posicao_coluna_final").val(posicoes[2]);
        }
    });
}

$(document).ajaxComplete(function() {
    rack_color();
    const col_in = $("#id_posicao_coluna_inicial").val();
    const col_fi = $("#id_posicao_coluna_final").val();
    const lin_in = $("#id_posicao_linha_inicial").val();
    const lin_fi = $("#id_posicao_linha_final").val();
    if (col_in) {
        $("#show_field").append(`${lin_in}${col_in}  (${lin_in}${col_in} - ${lin_fi}${col_fi})`);
    }
});