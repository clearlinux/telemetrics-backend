/*
 * Copyright (C) 2017-2020 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

(function(root, factory){

    root.telemetryUI = factory(root);

})(this, function(rootObj){

    function newChart(ctx, type, data, options) {
        new Chart(ctx, {
                type: type,
                data: data,
                options: options
            });
    }

    return {
        backgroundColors: ["#3e95cd", "#8e5ea2","#3cba9f","#e8c3b9","#c45850",
                           "#ff8c00", "#483d8b", "#00bfff", "#1e90ff", "#008000",
                           "#df42f4", "#c7f441", "#f47641", "#f44141", "#43f441"],
        newChart: newChart,
    };

});
