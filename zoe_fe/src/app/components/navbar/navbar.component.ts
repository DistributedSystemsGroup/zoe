import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service'

@Component({
  selector: 'navbar',
  template: `
        <nav class="navbar navbar-default navbar-fixed-top">
          <div class="container-fluid">
            <div class="navbar-header">
              <button type="button" class="collapsed navbar-toggle" data-toggle="collapse" data-target="#navbar-collapse" aria-expanded="false">
                <span class="sr-only">Toggle navigation</span>
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
              </button>
              <a [routerLink]="['']" class="navbar-brand">Zoe</a>
            </div>
            <div class="collapse navbar-collapse" id="navbar-collapse" *ngIf="isUserLogged()">
              <ul class="nav navbar-nav">
                <li [routerLinkActive]="['active']"><a [routerLink]="['/executions/list']">Executions list</a></li>
                <li [routerLinkActive]="['active']"><a [routerLink]="['/executions/new']">New Execution</a></li>
              </ul>
              <ul class="nav navbar-nav navbar-right">
                <li><a (click)="logout()"><i class="fa fa-power-off" aria-hidden="true"></i> Logout</a></li>
              </ul>
            </div>
          </div>
        </nav>
    `
})
export class NavbarComponent {
  constructor(private apiService: ApiService) { }

  isUserLogged(): Boolean {
    return this.apiService.isUserLoggedIn()
  }

  logout() {

  }
}
