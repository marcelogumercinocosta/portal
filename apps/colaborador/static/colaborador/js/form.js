
///// funcao para corrigir os casmpos que somem do vinculo
function combo_vinculo() {
    if ($('#id_vinculo').length) {
        $(".field-data_fim").hide();
        $(".field-empresa").hide();
        $(".field-registro_inpe").hide();
        $(".field-responsavel").hide();
        if ($('#id_vinculo').val() === '') { return; }
        if ($('#id_vinculo').val() == "3") {  //se for servidor
            $(".field-registro_inpe").show();
            $('#id_registro_inpe').rules('add', { required: true });
            $('#id_responsavel').rules( "remove" );
        } else if ($('#id_vinculo').val() == "4") { //se for terceiro
            $(".field-data_fim").show();
            $(".field-empresa").show();
            $('#id_data_fim').rules('add', { required: true });
            $('#id_empresa').rules('add', { required: true });
            $('#id_responsavel').rules('add', { required: true });
            $(".field-responsavel").show();
        } else {
            $(".field-data_fim").show();
            $(".field-responsavel").show();
            $('#id_data_fim').rules('add', { required: true });
            $('#id_responsavel').rules('add', { required: true });
        }
    }
}

$(document).ready(function () {

    const queryString = window.location.search;
    const urlParams = new URLSearchParams(queryString);

    // Validacao do email
    $.validator.addMethod("email_inpe", function (value, element) {
        if (urlParams.get('motivo') != "atualizar")
            return true;
        else
            return this.optional(element) || /^[a-zA-Z0-9.!#$%&'*+\/=?^_`{|}~-]+@(inpe.br)$/.test(value);
    }, 'Forneça um email do inpe válido.');

        
        

    if (urlParams.get('motivo') == "externo") {
        $('#id_externo').prop('checked',true);
        $('#id_externo').attr('disabled', 'disabled');
        $('#id_vinculo').find('[value=3]').remove();
        $('#id_vinculo').find('[value=5]').remove();
        $('#id_vinculo').selectpicker('refresh');
    } else { 
        $(".field-externo").hide();
    }

    //Validacao do formulario
    $("#_form").validate({
        rules: {
            first_name: { required: true, minlength: 3 },
            last_name: { required: true, minlength: 3 },
            email: { required: true, email_inpe: true },
            externo: { externo: true },
            telefone: { required: true, minlength: 8 },
            data_nascimento: { required: true },
            rg: { required: true },
            cpf: { required: true },
            cep: { required: true },
            endereco: { required: true },
            estado: { required: true },
            numero: { required: true },
            cidade: { required: true },
            bairro: { required: true },
            unidade: { required: true },
            predio: { required: true },
            nacionalidade: { required: true },
            contato_de_emergencia_nome: { required: true },
            contato_de_emergencia_parentesco: { required: true },
            contato_de_emergencia_telefone: { required: true },
            nacionalidade: { required: true },
            area_formacao: { required: true },
            data_inicio: { required: true },
            data_nascimento: { required: true },
            vinculo: { required: true, min: 2 },
            ramal: { required: true },
            password: { required: true, minlength: 10, pwcheck: true, },
            confirm_password: { required: true, equalTo: "#id_password" },
            data_inicio: { required: true },
        },
        messages: {
            confirm_password: "As senhas devem ser iguais",
            telefone: { minlength: "Por favor, forneça ao menos {0} caracteres.", },
            email: { email: "Forneça um email válido", },
            password: {
                pwcheck: "Forneça uma senha forte",
                minlength: "Por favor, forneça ao menos {0} caracteres.",
            }
        },
        errorElement: 'span',
        errorPlacement: function ( error, element ) {
            // Add the `help-block` class to the error element
            error.prependTo($(element).parents(".form-row-box").find('.form-row-error'));
        },
        highlight: function (element, errorClass, validClass) {
            $(element).addClass('is-invalid');
        },
        unhighlight: function (element, errorClass, validClass) {
            $(element).removeClass('is-invalid');
        },
        submitHandler: function (form) {
            // # TODO Veriricar isso
            neou_cms.remove_error_messages(); 
        },
    });

    // Esconde a data_fim se for servidor
    combo_vinculo()
    $("select#id_vinculo").change(function () {
        combo_vinculo()
    });

    // Deixar as mensagens do validate em portugues
    $.extend($.validator.messages, {
        required: "Campo obrigat&oacute;rio!",
    });

    //Mascaras
    $('#id_telefone').mask('(00) 0000-00009');
    $('#id_contato_de_emergencia_telefone').mask('(00) 0000-00009');
    $('#id_ramal').mask('0000');
    $('#id_cpf').mask('999.999.999-99');
    $('#id_cep').mask('99999-999');
    $('#id_data_nascimento').mask('99/99/9999');
    $('#id_data_inicio').mask('99/99/9999');
    $('#id_data_fim').mask('99/99/9999');
});




