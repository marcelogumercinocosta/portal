
$(document).ready(function(){
	$("input[name=cep]").blur(function(){
		var cep = $(this).val().replace(/[^0-9]/, '');
			$("#id_estado").siblings('label').addClass('active');

		if(cep){
			var url = 'https://viacep.com.br/ws/' + cep + '/json/';
			$.ajax({
				url: url,
				dataType: 'jsonp',
				crossDomain: true,
				contentType: "application/json",
				success : function(json){
					$("input[name=numero]").val('');
					if(json.bairro != null && json.bairro != '') { $("input[name=bairro]").val(json.bairro); }
					if(json.localidade != null && json.localidade != '') { $("input[name=cidade]").val(json.localidade); }
					if(json.uf != null && json.uf != '') { $("input[name=estado]").val(json.uf); }
					if(json.logradouro != null && json.logradouro != '') { $("input[name=endereco]").val(json.logradouro); }
				}
			});
		}
	});
});
