import { Pipe, PipeTransform } from '@angular/core';

import * as moment from 'moment';

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
