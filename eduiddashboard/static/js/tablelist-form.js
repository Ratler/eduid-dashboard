/*jslint vars: false, nomen: true, browser: true */
/*global $, console, alert, tabbedform */


(function () {
    "use strict";

    var sendInfo = function(container, cls, msg) {
            var messageHTML = '<div class="alert alert-' + cls +
    '"><button type="button" class="close" data-dismiss="alert">&times;</button>' +
            msg + '</div>';
            container.find('.info-container').prepend(messageHTML);
        },

        askCode = function(actions_url, action, container, value, title, placeholder) {
            askDialog(value, title, '', placeholder, function(code) {
                $.post(actions_url, {
                    action: action,
                    identifier: value,
                    code: code
                },
                function(data, statusText, xhr) {
                    sendInfo(container.find('#askDialog'), data.result, data.message);
                    if (data.result == 'ok') {
                        container.find('.btn').hide();
                        container.find('.btn').hide();
                        container.find('.divDialogElements').hide();
                        container.find('.finish-button').show();
                    }
                },
                'json')});
        },

        initialize = function (container, url) {
            if (container.find('.form-content .alert-error').length > 0){
                container.find('.form-content').show();
            }

            container.find('.add-new').click(function (e) {
                container.find('.form-content').toggleClass('hide');
                container.find('.add-new').toggleClass('active');
            });

            container.find('.resend-code').click(function(e) {
                var actions_url = $(this).attr('href'),
                    value = $(this).attr('data-identifier'),
                    dialog = $(this).parents('#askDialog');

                e.preventDefault();

                $.post(actions_url, {
                    action: 'resend_code',
                    identifier: value
                },
                function(data, statusText, xhr) {
                    sendInfo(dialog, data.result, data.message);
                },
                'json');
            });

            container.find('a.verifycode').click(function (e) {
                var identifier = $(e.target).attr('data-identifier');
                e.preventDefault();
                container.find('table.table .mobile-row[data-identifier=' + identifier + '] input[name=verify]').click();
            });

            container.find('table.table input[type=radio]').click(function (e) {
                var action = $(e.target).attr('name'),
                    value = $(e.target).val(),
                    actions_url = $('.actions-url').attr('data-url');

                container.find('.form-content').addClass('hide');
                container.find('.add-new').removeClass('active');

                $.post(actions_url, {
                    action: action,
                    identifier: value
                },
                function(data, statusText, xhr) {
                    if (data.result == 'getcode') {
                        askCode(actions_url, action, container, value, data.message, data.placeholder);
                    } else {
                        sendInfo(container, data.result, data.message);
                        if(data.action == 'remove' && data.result == 'ok') {
                            // special case of removing rows
                            container.find('table.table tr[data-identifier=' + data.identifier +']').remove();
                        }
                        $('body').trigger('action-executed');
                    }
                },
                'json');
            });
    };
    tabbedform.changetabs_calls.push(initialize);
}());
