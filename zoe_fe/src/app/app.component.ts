import { Component } from '@angular/core';

@Component({
  selector: 'app-zoe',
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
