jQuery(document).ready(function(){

// run locally
env = window.location.host;
if(env.match(/local/g)) {  }
	
	
// clear input
$('.default-value').each(function() {
	var default_value = this.value;

	$(this).focus(function() {
		if(this.value == default_value) {
			this.value = '';
		}
	});
	$(this).blur(function() {
		if(this.value == '') {
			this.value = default_value;
		}
	});
});

	
		
});
