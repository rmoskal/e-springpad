jQuery(document).ready(function() { 
	
	jQuery('.default-value').each(function() {
		var default_value = this.value;
		jQuery(this).focus(function() {
			if(this.value == default_value) {
			this.value = '';
			}
		});
		jQuery(this).blur(function() {
			if(this.value == '') {
				this.value = default_value;
			}
		});
	});
	
	jQuery('#password-clear').show();
	jQuery('#password-password').hide();
	
	jQuery('#password-clear').focus(function() {
		jQuery('#password-clear').hide();
		jQuery('#password-password').show();
		jQuery('#password-password').focus();
	});
	jQuery('#password-password').blur(function() {
		if(jQuery('#password-password').val() == '') {
		jQuery('#password-clear').show();
		jQuery('#password-password').hide();
		}
	});
	
});
