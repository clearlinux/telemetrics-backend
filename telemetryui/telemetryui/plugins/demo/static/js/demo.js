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

function initDemoButton() {

    document.getElementById("plugin-button").addEventListener("click", function(){
        if(jQuery(document.getElementById("plugin-title")).hasClass("red")){
            jQuery(document.getElementById("plugin-title")).removeClass("red")
            jQuery(document.getElementById("plugin-title")).addClass("blue");
        } else if(jQuery(document.getElementById("plugin-title")).hasClass("blue")){
            jQuery(document.getElementById("plugin-title")).removeClass("blue");
            jQuery(document.getElementById("plugin-title")).addClass("red");
        } else {
            jQuery(document.getElementById("plugin-title")).addClass("red");
        }
    })

}

initDemoButton();
