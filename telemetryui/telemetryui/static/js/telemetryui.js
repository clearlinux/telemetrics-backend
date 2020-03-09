/*
 * Copyright (C) 2017-2020 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

(function(root, factory){

    root.telemetryUI = factory(root);

})(this, function(rootObj){


    function newChart(ctx, type, data, options) {
        new Chart(ctx,
            {
                type: type,
                data: data,
                options: options
            });
    }


    function initTabs() {
        if (window.location.pathname !== "/telemetryui/") {
            var pathname = window.location.pathname;
            var leading_path = pathname.split('/').slice(0,3).join('/');
            if (pathname.search('\/plugins\/') > 0) {
                leading_path = pathname.split('/').slice(0,4).join('/');
            }
            jQuery("ul.nav.nav-tabs li a").removeClass("active");
            jQuery('ul.nav.nav-tabs li a[href^="' + leading_path + '"]').addClass("active");
        }
    }


    return {
        backgroundColors: ["#3e95cd", "#8e5ea2","#3cba9f","#e8c3b9","#c45850",
                           "#ff8c00", "#483d8b", "#00bfff", "#1e90ff", "#008000",
                           "#df42f4", "#c7f441", "#f47641", "#f44141", "#43f441"],
        newChart: newChart,
        initTabs: initTabs
    };

});
