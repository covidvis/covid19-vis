$('.default-open').addClass('active').click();

function openTabs(evt, tabs_class) {
    // Get all elements at same level with class='tab-content' and hide them
    $(tabs_class).parent().children('.tab-content').css('display', 'none');

    // Get all elements in this button group remove the class 'active'
    var button = $(evt.currentTarget);
    button.parent().children().removeClass('active');

    // Show the current tab, and add an 'active' class to the button that opened the tab
    $(tabs_class).css('display', 'block');
    button.addClass('active');
}
