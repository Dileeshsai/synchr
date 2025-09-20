import $ from "jquery";

class ImageUpload {
  constructor() {
    this.events();
  }

  // Events
  events() {
    // Change image on upload - use event delegation for dynamic content
    $(document).on("change", ".oh-upload-input", this.uploadImage.bind(this));
    // Remove uploaded image preview - use event delegation for dynamic content
    $(document).on("click", ".oh-remove-image", this.removeImage.bind(this));
  }

  /**
   *  Upload Image
   */

  uploadImage(e) {
    let inputEl = e.target.closest('.oh-upload-input');
    let targetSelector = inputEl.dataset.target;
    this.readUploadPath(inputEl, targetSelector);
  }
  readUploadPath(input, renderTarget) {
    if (input.files && input.files[0]) {
      var reader = new FileReader();

      reader.onload = function (e) {
        $(renderTarget).attr("src", e.target.result);
      };

      reader.readAsDataURL(input.files[0]);
    }
  }
 /**
   *  Remove Uploaded Image Preview
   */
  removeImage(e){
    e.preventDefault();
    let clickedEl = $(e.target).closest('.oh-remove-image');
    let targetSelector = clickedEl.data('target');
    let inputEl = clickedEl.closest('.oh-profile-section__image-container').find('.oh-upload-input');
    
    // Reset the image to default
    $(targetSelector).attr('src', '/static/images/ui/user.jpg');
    // Clear the specific input file
    inputEl.val('');
  }
}

export default ImageUpload;
