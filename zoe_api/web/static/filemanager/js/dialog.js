/**
 * jQuery UI dialog windows
 */

$(function() {
    $("#dialog_newfile").dialog(
        {
            autoOpen: false,
            buttons: [
                {
                    text: "Create",
                    click: function() {
                        var filename = $('#newfilename').val();
                        if (filename) {
                            sendRequest('create_file', {'name': filename});
                        }
                    }
                },
                {
                    text: "Cancel",
                    click: function() {
                        $(this).dialog("close");
                    }
                }
            ],
            close: function(e, ui) {
                $('#newfile_error').text('');
                $('#newfilename').val('');
            }
        }
    );

    $(function() {
        $("#dialog_newdir").dialog(
            {
                autoOpen: false,
                buttons: [
                    {
                        text: "Create",
                        click: function() {
                            var dirname = $('#newdirname').val();
                            if (dirname) {
                                sendRequest('create_dir', {'name': dirname});
                            }
                        }
                    },
                    {
                        text: "Cancel",
                        click: function() {
                            $(this).dialog("close");
                        }
                    }
                ],
                close: function(e, ui) {
                    $('#newdir_error').text('');
                    $('#newdirname').val('');
                }
            })
    });

    $("#dialog_error").dialog(
        {
            autoOpen: false,
            buttons: [
                {
                    text: "OK",
                    click: function() {
                        $(this).dialog("close");
                    }
                }
            ]
        }
    );

    $("#dialog_wait").dialog(
        {
            autoOpen: false,
            closeOnEscape: false,
            open: function(event, ui) { $(".ui-dialog-titlebar-close", this.parentNode).hide(); }
        }
    );

    $("#dialog_properties").dialog(
        {
            autoOpen: false,
            buttons: [
                {
                    text: "Save",
                    click: function() {

                    }
                },
                {
                    text: "Cancel",
                    click: function() {
                        $(this).dialog("close");
                    }
                }
            ]
        }
    );
});
