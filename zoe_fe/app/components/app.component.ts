import { Component } from '@angular/core';

@Component({
    selector: 'zoe',
    template: `
        <navbar></navbar>
            
        <div class="container body">
          <div class="main_container">
            <router-outlet></router-outlet>
          </div>
        </div>
    `
})

export class AppComponent {
    
}