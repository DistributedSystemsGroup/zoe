import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'toDate'
})
export class ToDatePipe implements PipeTransform {

  transform(value:any) {
    if (value) {
      return moment.unix(value).toDate();
    }
    return value;
  }

}
