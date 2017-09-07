/*
 * Copyright 2017 Intel Corporation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 */

(function(root, factory){

    root.telemetryUI = factory(root);

})(this, function(rootObj){


    function newChart(ctx, type, data, options){
        new Chart(ctx,
            {
                type: type,
                data: data,
                options: options
            });
    }

    function initTabs(){
        if (window.location.pathname !== "/telemetryui/") {
            jQuery("ul.nav.nav-tabs li").removeClass("active");
            jQuery('ul.nav.nav-tabs li a[href*="' + window.location.pathname + '"]').parent().addClass("active");
        }
    }

    return {
        backgroundColors: ["#3e95cd", "#8e5ea2","#3cba9f","#e8c3b9","#c45850",
                           "#ff8c00", "#483d8b", "#00bfff", "#1e90ff", "#008000",
                           "#df42f4", "#c7f441", "#f47641", "#f44141", "#43f441"],
        newChart: newChart
    };

});
