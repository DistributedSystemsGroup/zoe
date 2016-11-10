import { Injectable } from '@angular/core'
import { Headers } from "@angular/http";
import { Credentials } from "../entities/credentials";

let AUTH_HEADER: string = 'authHeader'
let USERNAME: string = 'username'
let ROLE: string = 'role'

@Injectable()
export class StorageService {
  setAuthHeader(headers:Headers) {
    sessionStorage.setItem(AUTH_HEADER, headers.get("authorization"))
  }

  getAuthHeader():Headers {
    let auth = sessionStorage.getItem(AUTH_HEADER)
    if (auth == null)
      return null

    var headers = new Headers
    headers.append('Authorization', auth)
    return headers
  }

  removeAuthHeader() {
    sessionStorage.removeItem(AUTH_HEADER)
  }

  setUsername(username:string) {
    sessionStorage.setItem(USERNAME, username)
  }

  getUsername():string {
    return sessionStorage.getItem(USERNAME)
  }

  removeUsername() {
    sessionStorage.removeItem(USERNAME)
  }

  setRole(role:string) {
    sessionStorage.setItem(ROLE, role)
  }

  getRole():string {
    return sessionStorage.getItem(ROLE)
  }

  removeRole() {
    sessionStorage.removeItem(ROLE)
  }

  setCredentials(credentials:Credentials) {
    this.setUsername(credentials.username)
    this.setRole(credentials.role)
  }

  getCredentials(): Credentials {
    let username = this.getUsername();
    let role = this.getRole();

    if (username == null || role == null)
      return null;

    let credentials = new Credentials();
    credentials.username = username;
    credentials.role = role;

    return credentials;
  }

  removeCredentials() {
    this.removeUsername();
    this.removeRole();
  }
}